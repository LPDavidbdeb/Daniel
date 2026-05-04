from django.db import transaction
from django.contrib.auth import get_user_model
from students.models import Student, StudentState, StateTransitionLog
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from typing import Optional, Any, Union

User = get_user_model()

class IllegalTransitionError(Exception):
    """Raised when a state transition violates business invariants."""
    pass

def apply_event(
    student: Student,
    academic_year: str,
    event_name: str,
    new_workflow_state: Optional[WorkflowState] = None,
    new_final_april_state: Optional[FinalAprilState] = None,
    new_vetting_status: Optional[VettingStatus] = None,
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
        # Fetch StudentState with row-level lock for concurrency safety
        state = StudentState.objects.select_for_update().get(
            student=student, 
            academic_year=academic_year
        )

        from_workflow_state = state.workflow_state
        from_final_state = state.final_april_state

        # --- Transition Guards (Invariants) ---
        
        # Invariant 1: Cannot move out of finalized state unless specifically allowed (placeholder logic)
        # If final_april_state is set, we consider the student "finalized" for that year.
        if from_final_state and new_workflow_state == WorkflowState.REGULAR_REVIEW_PENDING:
             raise IllegalTransitionError(
                 f"Cannot return to {WorkflowState.REGULAR_REVIEW_PENDING} once a final state is assigned."
             )

        # Invariant 2: Pedagogical Guards (US2.2)
        validate_transition(
            student=student,
            academic_year=academic_year,
            from_workflow_state=from_workflow_state,
            new_workflow_state=new_workflow_state,
            new_final_april_state=new_final_april_state
        )

        # --- Persistence ---
        
        # Update ledger
        if new_workflow_state:
            state.workflow_state = new_workflow_state
        if new_final_april_state:
            state.final_april_state = new_final_april_state
        if new_vetting_status:
            state.vetting_status = new_vetting_status
            
        state.version += 1
        state.save()

        # Write Audit Log
        StateTransitionLog.objects.create(
            student=student,
            from_state=from_workflow_state,
            to_state=new_workflow_state or from_workflow_state, # Simplified for workflow tracking
            event_name=event_name,
            actor=actor,
            reason_payload={
                **payload,
                "version": state.version,
                "updated_final_state": new_final_april_state,
                "updated_vetting_status": new_vetting_status
            }
        )

        return state
