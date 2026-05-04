from django.db import transaction
from django.contrib.auth import get_user_model
from students.models import Student, StudentState, StateTransitionLog
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from typing import Optional, Any

User = get_user_model()

class IllegalTransitionError(Exception):
    """Raised when a state transition violates business invariants."""
    pass

class SnapshotClosureError(Exception):
    """Raised when the April snapshot cannot be closed due to incomplete vetting."""
    def __init__(self, incomplete_students: list[dict]):
        self.incomplete_students = incomplete_students
        names = ", ".join([s['full_name'] for s in incomplete_students])
        super().__init__(f"Cannot close snapshot. Incomplete vetting for: {names}")

def apply_event(
    student: Student,
    academic_year: str,
    event_name: str,
    new_workflow_state: Optional[WorkflowState] = None,
    new_final_april_state: Optional[FinalAprilState] = None,
    new_vetting_status: Optional[VettingStatus] = None,
    new_reason_codes: Optional[dict] = None,  # ← FIX US1.2
    actor: Optional[User] = None,
    payload: Optional[dict[str, Any]] = None
) -> StudentState:
    """
    Central orchestration gateway for student state transitions.
    Enforces business invariants, ensures concurrency safety, and writes audit logs.
    """
    from students.services.transition_guards import validate_transition

    if payload is None:
        payload = {}

    # Validate enums if provided
    if new_workflow_state and new_workflow_state not in WorkflowState.values:
        raise IllegalTransitionError(f"Invalid workflow state: {new_workflow_state}")
    if new_final_april_state and new_final_april_state not in FinalAprilState.values:
        raise IllegalTransitionError(f"Invalid final April state: {new_final_april_state}")
    if new_vetting_status and new_vetting_status not in VettingStatus.values:
        raise IllegalTransitionError(f"Invalid vetting status: {new_vetting_status}")

    with transaction.atomic():
        # FIX US2.1: Handle missing student state explicitly
        try:
            state = StudentState.objects.select_for_update().get(
                student=student,
                academic_year=academic_year
            )
        except StudentState.DoesNotExist:
            raise IllegalTransitionError(
                f"Student state not seeded for {academic_year}. "
                f"Run management command seed_student_states first."
            )

        # FIX US2.1: Check is_active
        if not student.is_active:
            raise IllegalTransitionError(
                f"Cannot apply event to inactive student {student.fiche}"
            )

        from_workflow_state = state.workflow_state
        from_final_state = state.final_april_state

        # --- Transition Guards (Invariants) ---
        validate_transition(
            student=student,
            academic_year=academic_year,
            from_workflow_state=from_workflow_state,
            new_workflow_state=new_workflow_state,
            new_final_april_state=new_final_april_state
        )
        
        # Invariant 1: Cannot return from finalized state to workflow review
        # (FIX US2.1: Broaden to prevent any semantic regression)
        if from_final_state:
            # Cannot change final_april_state once assigned
            if new_final_april_state and new_final_april_state != from_final_state:
                allowed_summer_switch = {
                    FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER,
                    FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
                }
                if {from_final_state, new_final_april_state} != allowed_summer_switch:
                    raise IllegalTransitionError(
                        f"Cannot overwrite final April state {from_final_state} "
                        f"with {new_final_april_state}. Student is already finalized."
                    )

            # Cannot go back to workflow review
            if new_workflow_state == WorkflowState.REGULAR_REVIEW_PENDING:
                raise IllegalTransitionError(
                    f"Cannot return to {WorkflowState.REGULAR_REVIEW_PENDING} once a final state is assigned."
                )

        # --- Persistence ---
        from students.models import SummerSchoolEnrollment
        from school.models import Course

        # Update ledger
        if new_workflow_state:
            state.workflow_state = new_workflow_state
        if new_final_april_state:
            state.final_april_state = new_final_april_state
        if new_vetting_status:
            state.vetting_status = new_vetting_status
        # FIX US1.2: Persist reason_codes
        if new_reason_codes is not None:
            state.reason_codes = new_reason_codes

        state.version += 1
        state.save()

        # --- Side-effect: Summer School Synchronization (US3.2) ---
        sync_payload = {}

        if state.final_april_state == FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER:
            course_id = payload.get("course_id")
            if course_id:
                # FIX NEW: Handle DoesNotExist gracefully
                try:
                    course = Course.objects.get(id=course_id)
                    SummerSchoolEnrollment.objects.update_or_create(
                        student=student,
                        academic_year=academic_year,
                        defaults={
                            "course": course,
                            "enrolled_by": actor
                        }
                    )
                    sync_payload["legacy_summer_sync"] = "CREATED_OR_UPDATED"
                    sync_payload["summer_sync"] = "CREATED_OR_UPDATED"
                    sync_payload["course_code"] = course.local_code
                except Course.DoesNotExist:
                    raise IllegalTransitionError(
                        f"Cannot enroll in summer course: course ID {course_id} not found"
                    )
        else:
            # If state is NOT promote with summer, ensure no enrollment exists
            deleted_count, _ = SummerSchoolEnrollment.objects.filter(
                student=student,
                academic_year=academic_year
            ).delete()
            if deleted_count > 0:
                sync_payload["legacy_summer_sync"] = "DELETED"
                sync_payload["summer_sync"] = "DELETED"

        # Write Audit Log
        # FIX US1.3: to_state fallback should be informative, not empty string
        to_state_value = (
            new_workflow_state
            or from_workflow_state
            or (f"FINAL_STATE_ONLY:{new_final_april_state}" if new_final_april_state else "NO_STATE_CHANGE")
        )

        StateTransitionLog.objects.create(
            student=student,
            from_state=from_workflow_state,
            to_workflow_state=new_workflow_state,
            to_final_april_state=new_final_april_state,
            to_state=to_state_value,
            event_name=event_name,
            actor=actor,
            reason_payload={
                **payload,
                **sync_payload,
                **(new_reason_codes or {}),
                "version": state.version,
                "updated_final_state": new_final_april_state,
                "updated_vetting_status": new_vetting_status,
                "reason_codes": new_reason_codes
            }
        )

        return state


def close_april_snapshot(academic_year: str) -> bool:
    """
    Validates that all active students for the year have been vetted.
    Blocks closure if:
    1. Any active student is still in REQUIRES_REVIEW
    2. Any active student has no StudentState row (invisible, unseeded)
    """
    # Check 1: Incomplete vettings
    incomplete_vettings = StudentState.objects.filter(
        academic_year=academic_year,
        student__is_active=True,
        vetting_status=VettingStatus.REQUIRES_REVIEW
    ).select_related('student').values('student__fiche', 'student__full_name')

    students_list = [
        {'fiche': s['student__fiche'], 'full_name': s['student__full_name']}
        for s in incomplete_vettings
    ]

    # Check 2: Invisible students (active but no state row at all) — FIX US2.4
    invisible_students = Student.objects.filter(
        is_active=True,
        states__isnull=True,
    ).values('fiche', 'full_name')

    invisible_list = [
        {'fiche': s['fiche'], 'full_name': s['full_name']}
        for s in invisible_students
    ]

    # Combine both lists
    all_incomplete = students_list + invisible_list

    if all_incomplete:
        raise SnapshotClosureError(incomplete_students=all_incomplete)

    return True
