from typing import Dict, List, Tuple
from students.models import Student, AcademicResult, StudentPromotionOverride
from students.enums import (
    WorkflowState,
    FinalAprilState,
    VettingStatus,
    CourseEvalState,
)
from students.constants import (
    PASS_THRESHOLD,
    FAIL_HARD_BLOCK_THRESHOLD,
    TEACHER_REVIEW_MIN,
    TEACHER_REVIEW_MAX,
    SUMMER_ELIGIBLE_MIN,
    SUMMER_ELIGIBLE_MAX,
)


def evaluate_course_result(
    result: AcademicResult,
) -> Tuple[CourseEvalState, str]:
    """
    MICRO-LEVEL ANALYSIS: Evaluates a single AcademicResult to determine its course-level state.

    Returns:
        Tuple[CourseEvalState, str]: (course_state, reason_code)
        reason_code format: "COURSE_CODE (grade%)"

    Logic:
    - Teacher Review Guard: 57-59 → TEACHER_REVIEW_PENDING
    - Summer Eligibility Guard: 50-56 on core course → SUMMER_ELIGIBLE, else FAILED
    - Failure Guard: < 50 → FAILED
    - Pass: >= 60 → PASS
    """
    grade = result.final_grade
    course_code = result.offering.course.local_code
    reason_code = f"{course_code} ({grade}%)"

    if grade is None:
        # Missing grades are treated as needing review
        return CourseEvalState.FAILED, reason_code

    # Teacher Review Guard: 57-59
    if TEACHER_REVIEW_MIN <= grade <= TEACHER_REVIEW_MAX:
        return CourseEvalState.TEACHER_REVIEW_PENDING, reason_code

    # Summer Eligibility Guard: 50-56
    if SUMMER_ELIGIBLE_MIN <= grade <= SUMMER_ELIGIBLE_MAX:
        if result.offering.course.is_core_or_sanctioned:
            # Core/sanctioned course in summer-eligible range
            return CourseEvalState.SUMMER_ELIGIBLE, reason_code
        else:
            # Non-core, non-sanctioned course in 50-56 range → FAILED
            return CourseEvalState.FAILED, reason_code

    # Failure Guard: < 50
    if grade < FAIL_HARD_BLOCK_THRESHOLD:
        return CourseEvalState.FAILED, reason_code

    # Pass: >= 60
    if grade >= PASS_THRESHOLD:
        return CourseEvalState.PASS, reason_code

    # Fallback (should not occur with proper constants)
    return CourseEvalState.FAILED, reason_code


def apply_level_policy(
    student_level: str,
    micro_states: Dict[str, CourseEvalState],
    reason_codes_by_state: Dict[CourseEvalState, List[str]],
) -> Tuple[WorkflowState, FinalAprilState | None, VettingStatus, Dict]:
    """
    Policy dispatcher that applies level-specific macro rules.

    This replaces the hard-coded Rule 3 (Auto-Promote) and Rule 4 (Hard Failure)
    with an injectable policy keyed by normalized student level.
    """
    # Normalize level to uppercase key (e.g. 'Sec 1' -> 'SEC_1')
    if not student_level:
        level_key = "DEFAULT"
    else:
        level_key = student_level.strip().upper().replace(" ", "_")

    # Default policies — conservative fallback
    def _has_hard_blocker():
        # Inspect failed course reason strings like "MAT101 (42%)" to detect < threshold
        hard_blockers = []
        for s in reason_codes_by_state.get(CourseEvalState.FAILED, []):
            try:
                # extract the number between parentheses
                if "(" in s and ")" in s:
                    part = s.split("(")[-1].split(")")[0]
                    grade_str = part.strip().rstrip('%')
                    grade = int(grade_str)
                    if grade < FAIL_HARD_BLOCK_THRESHOLD:
                        hard_blockers.append(s)
            except Exception:
                # ignore parse errors
                continue
        return hard_blockers

    def policy_sec_1():
        # Sec 1: be more lenient — non-hard failed courses lead to HOLDBACK; hard blockers escalate to IFP
        hard_blockers = _has_hard_blocker()
        if hard_blockers:
            return (
                WorkflowState.IFP_CANDIDATE_REVIEW,
                None,
                VettingStatus.REQUIRES_REVIEW,
                {
                    "message": "Level SEC_1 policy: hard blocker -> IFP_CANDIDATE_REVIEW",
                    "failed_courses": reason_codes_by_state.get(CourseEvalState.FAILED, []),
                    "hard_blockers": hard_blockers,
                    "rule": "HARD_FAILURE",
                },
            )
        if any(state == CourseEvalState.FAILED for state in micro_states.values()):
            return (
                WorkflowState.READY_FOR_FINALIZATION,
                FinalAprilState.APRIL_FINAL_HOLDBACK,
                VettingStatus.REQUIRES_REVIEW,
                {
                    "message": "Level SEC_1 policy: failed -> HOLDBACK",
                    "failed_courses": reason_codes_by_state.get(CourseEvalState.FAILED, []),
                    "rule": "LEVEL_SEC_1_HOLDBACK",
                },
            )
        # All pass -> regular promote
        if all(state == CourseEvalState.PASS for state in micro_states.values()):
            return (
                WorkflowState.READY_FOR_FINALIZATION,
                FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
                VettingStatus.AUTO_VETTED,
                {"message": "Level SEC_1 policy: all pass -> auto-promote", "rule": "LEVEL_AUTO_PROMOTE"},
            )
        # Fallback
        return (
            WorkflowState.REGULAR_REVIEW_PENDING,
            None,
            VettingStatus.REQUIRES_REVIEW,
            {"message": "Level SEC_1 policy fallback", "rule": "LEVEL_FALLBACK"},
        )

    def policy_sec_4():
        # Sec 4: stricter — any failed course is an IFP candidate review
        if any(state == CourseEvalState.FAILED for state in micro_states.values()):
            return (
                WorkflowState.IFP_CANDIDATE_REVIEW,
                None,
                VettingStatus.REQUIRES_REVIEW,
                {
                    "message": "Level SEC_4 policy: failed -> IFP_CANDIDATE_REVIEW",
                    "failed_courses": reason_codes_by_state.get(CourseEvalState.FAILED, []),
                    "rule": "LEVEL_SEC_4_IFP",
                },
            )
        if all(state == CourseEvalState.PASS for state in micro_states.values()):
            return (
                WorkflowState.READY_FOR_FINALIZATION,
                FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
                VettingStatus.AUTO_VETTED,
                {"message": "Level SEC_4 policy: all pass -> auto-promote", "rule": "LEVEL_AUTO_PROMOTE"},
            )
        return (
            WorkflowState.REGULAR_REVIEW_PENDING,
            None,
            VettingStatus.REQUIRES_REVIEW,
            {"message": "Level SEC_4 policy fallback", "rule": "LEVEL_FALLBACK"},
        )

    POLICY_MAP = {
        "SEC_1": policy_sec_1,
        "SEC_4": policy_sec_4,
        # Add other level-specific policies here as needed
    }

    policy_fn = POLICY_MAP.get(level_key)
    if policy_fn:
        return policy_fn()

    # Default conservative policy: treat failures as IFP candidate
    if any(state == CourseEvalState.FAILED for state in micro_states.values()):
        return (
            WorkflowState.IFP_CANDIDATE_REVIEW,
            None,
            VettingStatus.REQUIRES_REVIEW,
            {
                "message": "Hard failure detected - IFP Candidate Review",
                "failed_courses": reason_codes_by_state.get(CourseEvalState.FAILED, []),
                "rule": "HARD_FAILURE",
            },
        )

    # Default auto-promote when everything passes
    if all(state == CourseEvalState.PASS for state in micro_states.values()):
        return (
            WorkflowState.READY_FOR_FINALIZATION,
            FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
            VettingStatus.AUTO_VETTED,
            {"message": "All courses passed - Auto-promotion", "rule": "AUTO_PROMOTE"},
        )

    return (
        WorkflowState.REGULAR_REVIEW_PENDING,
        None,
        VettingStatus.REQUIRES_REVIEW,
        {"message": "Default policy fallback", "rule": "LEVEL_FALLBACK"},
    )


def aggregate_micro_results(
    micro_states: Dict[str, CourseEvalState],
    reason_codes_by_state: Dict[CourseEvalState, List[str]],
    student_level: str | None = None,
) -> Tuple[WorkflowState, FinalAprilState | None, VettingStatus, Dict]:
    """
    MACRO-LEVEL ANALYSIS: Aggregates micro-level course states into a student-level workflow state.

    Hierarchical Rules:
    1. **Absolute Priority (Teacher Review)**: If ANY course is TEACHER_REVIEW_PENDING
       → REGULAR_REVIEW_PENDING with REQUIRES_REVIEW
    2. **Secondary Priority (Summer Routing)**: If NO teacher review but ANY SUMMER_ELIGIBLE
       → READY_FOR_FINALIZATION with APRIL_FINAL_PROMOTE_WITH_SUMMER
    3. **All Pass**: If all courses are PASS
       → READY_FOR_FINALIZATION with APRIL_FINAL_PROMOTE_REGULAR
    4. **Hard Failure**: If ANY course is FAILED (including hard blockers)
       → IFP_CANDIDATE_REVIEW (pedagogical hold)

    Returns:
        Tuple[WorkflowState, FinalAprilState | None, VettingStatus, reason_payload]
    """
    # Count course states
    has_teacher_review = any(
        state == CourseEvalState.TEACHER_REVIEW_PENDING
        for state in micro_states.values()
    )
    has_summer_eligible = any(
        state == CourseEvalState.SUMMER_ELIGIBLE
        for state in micro_states.values()
    )
    has_failed = any(
        state == CourseEvalState.FAILED
        for state in micro_states.values()
    )
    all_pass = all(
        state == CourseEvalState.PASS
        for state in micro_states.values()
    )

    # Rule 1: Absolute Priority - Teacher Review
    if has_teacher_review:
        return (
            WorkflowState.REGULAR_REVIEW_PENDING,
            None,
            VettingStatus.REQUIRES_REVIEW,
            {
                "message": "Teacher Review PENDING - Absolute Priority",
                "teacher_review_courses": reason_codes_by_state.get(CourseEvalState.TEACHER_REVIEW_PENDING, []),
                "rule": "TEACHER_REVIEW_PRIORITY",
            }
        )

    # Rule 2: Secondary Priority - Summer Routing (only if no teacher review)
    if has_summer_eligible and not has_failed:
        return (
            WorkflowState.READY_FOR_FINALIZATION,
            FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER,
            VettingStatus.AUTO_VETTED,
            {
                "message": "Summer Eligible - Auto-routed to summer school",
                "summer_eligible_courses": reason_codes_by_state.get(CourseEvalState.SUMMER_ELIGIBLE, []),
                "rule": "SUMMER_ROUTING",
            }
        )

    # Delegate remaining decisions (auto-promote / hard-failure handling)
    # to a level-specific policy dispatcher.
    return apply_level_policy(student_level or None, micro_states, reason_codes_by_state)


def derive_student_state(student: Student, academic_year: str) -> dict:
    """
    TWO-LEVEL ARCHITECTURE: Derives suggested WorkflowState and FinalAprilState.

    LEVEL 1 (MICRO): Evaluate each AcademicResult individually
    LEVEL 2 (MACRO): Aggregate micro-level states into a student-level workflow state

    Process:
    1. Check for legacy manual overrides (highest precedence)
    2. Fetch all core course results for the student/year
    3. MICRO ANALYSIS: Evaluate each course result independently
    4. MACRO ANALYSIS: Aggregate micro results into workflow state
    5. Return comprehensive diagnostic payload
    """

    # 0. Check for legacy manual overrides (Highest Precedence)
    override = StudentPromotionOverride.objects.filter(
        student=student, 
        academic_year=academic_year
    ).first()

    if override:
        OVERRIDE_MAPPING = {
            'FORCE_PASS': (WorkflowState.READY_FOR_FINALIZATION, FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR),
            'FORCE_RETAKE': (WorkflowState.READY_FOR_FINALIZATION, FinalAprilState.APRIL_FINAL_HOLDBACK),
            'TRANSFER_IFP': (WorkflowState.IFP_CANDIDATE_REVIEW, FinalAprilState.APRIL_FINAL_IFP_N),
            'TRANSFER_DIM': (WorkflowState.IFP_CANDIDATE_REVIEW, FinalAprilState.APRIL_FINAL_HOLDBACK),
        }
        
        if override.override_type in OVERRIDE_MAPPING:
            w_state, f_state = OVERRIDE_MAPPING[override.override_type]
            return {
                "workflow_state": w_state,
                "final_april_state": f_state,
                "vetting_status": VettingStatus.MANUALLY_VETTED,
                "reason_codes": {
                    "message": f"Legacy override applied: {override.override_type}",
                    "legacy_override_applied": True,
                    "override_type": override.override_type
                }
            }

    # Fetch all results (core and non-core)
    results = AcademicResult.objects.filter(
        student=student, 
        academic_year=academic_year
    ).select_related('offering__course')

    # Filter to core courses only
    core_results = [r for r in results if r.offering.course.is_core_or_sanctioned]
    
    # Guard: No core results
    if not core_results:
        return {
            "workflow_state": WorkflowState.REGULAR_REVIEW_PENDING,
            "final_april_state": None,
            "vetting_status": VettingStatus.REQUIRES_REVIEW,
            "reason_codes": {
                "message": "MISSING_GRADES - No core course results found",
                "rule": "NO_CORE_RESULTS",
            }
        }

    # Guard: All grades are None
    if all(r.final_grade is None for r in core_results):
        return {
            "workflow_state": WorkflowState.REGULAR_REVIEW_PENDING,
            "final_april_state": None,
            "vetting_status": VettingStatus.REQUIRES_REVIEW,
            "reason_codes": {
                "message": "MISSING_GRADES - All core course grades are missing",
                "rule": "ALL_GRADES_MISSING",
            }
        }

    # ====== MICRO-LEVEL ANALYSIS ======
    # Evaluate EACH course result independently (no short-circuiting)
    micro_states: Dict[str, CourseEvalState] = {}
    reason_codes_by_state: Dict[CourseEvalState, List[str]] = {
        state: [] for state in CourseEvalState
    }

    for result in core_results:
        course_code = result.offering.course.local_code
        course_state, reason_code = evaluate_course_result(result)
        micro_states[course_code] = course_state
        reason_codes_by_state[course_state].append(reason_code)

    # ====== MACRO-LEVEL ANALYSIS ======
    # Aggregate micro results using strict hierarchy
    workflow_state, final_april_state, vetting_status, macro_payload = aggregate_micro_results(
        micro_states,
        reason_codes_by_state,
        student_level=student.level if hasattr(student, 'level') else None,
    )

    # Enrich payload with micro-level details
    macro_payload["micro_analysis"] = {
        "courses_evaluated": list(micro_states.keys()),
        "state_distribution": {
            state: len(codes)
            for state, codes in reason_codes_by_state.items()
            if codes
        },
    }

    return {
        "workflow_state": workflow_state,
        "final_april_state": final_april_state,
        "vetting_status": vetting_status,
        "reason_codes": macro_payload,
    }
