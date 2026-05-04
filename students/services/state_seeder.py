from students.models import (
    Student, StudentState, StateTransitionLog, 
    SummerSchoolEnrollment, StudentPromotionOverride
)
from students.enums import WorkflowState, FinalAprilState, VettingStatus

def seed_student_state(student: Student, academic_year: str) -> StudentState:
    """
    Seeds or updates the StudentState for a given student and academic year.
    Maps legacy records (SummerSchoolEnrollment, StudentPromotionOverride)
    to the new State Engine enums.
    """
    
    # Mapping for StudentPromotionOverride FINAL STATES
    FINAL_STATE_MAPPING = {
        'FORCE_PASS': FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
        'FORCE_RETAKE': FinalAprilState.APRIL_FINAL_HOLDBACK,
        'TRANSFER_IFP': FinalAprilState.APRIL_FINAL_IFP_N,
        'TRANSFER_DIM': FinalAprilState.APRIL_FINAL_HOLDBACK,
    }

    # Mapping for StudentPromotionOverride WORKFLOW STATES
    WORKFLOW_STATE_MAPPING = {
        'FORCE_PASS': WorkflowState.READY_FOR_FINALIZATION,
        'FORCE_RETAKE': WorkflowState.READY_FOR_FINALIZATION,
        'TRANSFER_IFP': WorkflowState.IFP_CANDIDATE_REVIEW,  # ← FIX US1.4
        'TRANSFER_DIM': WorkflowState.IFP_CANDIDATE_REVIEW,  # ← FIX US1.4
    }

    # Initial defaults
    workflow_state = WorkflowState.REGULAR_REVIEW_PENDING
    final_april_state = None
    vetting_status = VettingStatus.REQUIRES_REVIEW
    reason_codes = {
        "message": "Initial seeding from legacy data"
    }

    # Check for legacy records
    summer_enrollment = SummerSchoolEnrollment.objects.filter(
        student=student, academic_year=academic_year
    ).first()
    
    override = StudentPromotionOverride.objects.filter(
        student=student, academic_year=academic_year
    ).first()

    # 1. Check for Summer School Enrollment (takes precedence)
    if summer_enrollment:
        final_april_state = FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER
        vetting_status = VettingStatus.AUTO_VETTED
        reason_codes["legacy_summer_enrollment"] = "APRIL_FINAL_PROMOTE_WITH_SUMMER"
    # 2. Check for Overrides
    elif override and override.override_type in FINAL_STATE_MAPPING:
        workflow_state = WORKFLOW_STATE_MAPPING[override.override_type]
        final_april_state = FINAL_STATE_MAPPING[override.override_type]
        vetting_status = (
            VettingStatus.MANUALLY_VETTED
            if override.override_type in {'FORCE_PASS', 'FORCE_RETAKE'}
            else VettingStatus.AUTO_VETTED
        )
        reason_codes["legacy_override"] = override.override_type

    # Create or Update StudentState
    state, created = StudentState.objects.update_or_create(
        student=student,
        academic_year=academic_year,
        defaults={
            'workflow_state': workflow_state,
            'final_april_state': final_april_state,
            'vetting_status': vetting_status,
            'reason_codes': reason_codes,  # ← FIX US1.2: persist reason_codes
        }
    )

    # FIX US1.4: Only log on creation, not on update
    if created:
        StateTransitionLog.objects.create(
            student=student,
            from_state=None,
            to_state=workflow_state,
            event_name='SYSTEM_SEED_INITIALIZATION',
            actor=None,
            reason_payload={
                'message': 'Initial seeding from legacy data',
                'created': created,
                'legacy_summer': bool(summer_enrollment),
                'legacy_override': bool(override),
                'reason_codes': reason_codes
            }
        )

    return state


