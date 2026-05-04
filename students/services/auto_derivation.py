from students.models import Student, AcademicResult, StudentPromotionOverride
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from students.constants import PASS_THRESHOLD, FAIL_HARD_BLOCK_THRESHOLD, TEACHER_REVIEW_MIN

def derive_student_state(student: Student, academic_year: str) -> dict:
    """
    Evaluates AcademicResults to derive suggested WorkflowState and FinalAprilState.
    Prioritizes legacy manual overrides from StudentPromotionOverride.
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

    results = AcademicResult.objects.filter(
        student=student, 
        academic_year=academic_year
    ).select_related('offering__course')

    core_results = [r for r in results if r.offering.course.is_core_or_sanctioned]
    
    # Guard: No core results at all
    if not core_results:
        return {
            "workflow_state": WorkflowState.REGULAR_REVIEW_PENDING,
            "final_april_state": None,
            "vetting_status": VettingStatus.REQUIRES_REVIEW,
            "reason_codes": {
                "message": "MISSING_GRADES - No core course results found"
            }
        }

    # Guard: All grades are None
    if all(r.final_grade is None for r in core_results):
        return {
            "workflow_state": WorkflowState.REGULAR_REVIEW_PENDING,
            "final_april_state": None,
            "vetting_status": VettingStatus.REQUIRES_REVIEW,
            "reason_codes": {
                "message": "MISSING_GRADES - All core course grades are missing"
            }
        }

    # Analyze core course results
    failures = []
    hard_blockers = []
    teacher_review_needed = False
    failing_codes = []

    for res in core_results:
        grade = res.final_grade
        if grade is None:
            continue
            
        if grade < PASS_THRESHOLD:
            failures.append(res)
            failing_codes.append(res.offering.course.local_code)
            
            if grade < FAIL_HARD_BLOCK_THRESHOLD:
                hard_blockers.append(res)
            
            if TEACHER_REVIEW_MIN <= grade < PASS_THRESHOLD:
                teacher_review_needed = True

    # Rule Matrix
    
    # Rule 4: IFP / Holdback Candidate (>1 failure OR any hard blocker)
    if len(failures) > 1 or len(hard_blockers) > 0:
        return {
            "workflow_state": WorkflowState.IFP_CANDIDATE_REVIEW,
            "final_april_state": None,
            "vetting_status": VettingStatus.REQUIRES_REVIEW,
            "reason_codes": {
                "message": "Multiple failures or hard blocker detected",
                "failures": failing_codes,
                "hard_blocker": len(hard_blockers) > 0
            }
        }

    # Rule 2: Teacher Review Queue (any core course 57-59 AND no hard blockers)
    # We already checked for hard blockers above.
    if teacher_review_needed:
        return {
            "workflow_state": WorkflowState.REGULAR_REVIEW_PENDING,
            "final_april_state": None,
            "vetting_status": VettingStatus.REQUIRES_REVIEW,
            "reason_codes": {
                "message": "Teacher Review Needed (Grade 57-59)",
                "failures": failing_codes
            }
        }

    # Rule 3: Summer School Queue (exactly ONE core course failure 50-59)
    if len(failures) == 1:
        # We know it's not a hard blocker and not in teacher review range 
        # (because it didn't trigger the above rules).
        return {
            "workflow_state": WorkflowState.READY_FOR_FINALIZATION,
            "final_april_state": FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER,
            "vetting_status": VettingStatus.AUTO_VETTED,
            "reason_codes": {
                "message": "Eligible for Summer School",
                "failures": failing_codes
            }
        }

    # Rule 1: Auto-Promote (all core courses >= 60)
    return {
        "workflow_state": WorkflowState.READY_FOR_FINALIZATION,
        "final_april_state": FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
        "vetting_status": VettingStatus.AUTO_VETTED,
        "reason_codes": {
            "message": "Auto-promotion",
            "failures": []
        }
    }
