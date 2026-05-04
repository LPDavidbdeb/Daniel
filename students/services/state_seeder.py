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
    
    # Mapping for StudentPromotionOverride types
    OVERRIDE_MAPPING = {
        'FORCE_PASS': FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
        'FORCE_RETAKE': FinalAprilState.APRIL_FINAL_HOLDBACK,
        'TRANSFER_IFP': FinalAprilState.APRIL_FINAL_IFP_N,
        'TRANSFER_DIM': FinalAprilState.APRIL_FINAL_HOLDBACK,
    }

    # Initial defaults
    workflow_state = WorkflowState.REGULAR_REVIEW_PENDING
    final_april_state = None
    vetting_status = VettingStatus.REQUIRES_REVIEW
    
    # 1. Check for Summer School Enrollment (takes precedence in US1.4 description)
    summer_enrollment = SummerSchoolEnrollment.objects.filter(
        student=student, academic_year=academic_year
    ).first()
    
    if summer_enrollment:
        final_april_state = FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER
        vetting_status = VettingStatus.AUTO_VETTED
    else:
        # 2. Check for Overrides
        override = StudentPromotionOverride.objects.filter(
            student=student, academic_year=academic_year
        ).first()
        
        if override and override.override_type in OVERRIDE_MAPPING:
            final_april_state = OVERRIDE_MAPPING[override.override_type]
            vetting_status = VettingStatus.AUTO_VETTED # Overrides are manually vetted by definition

    # Create or Update StudentState
    state, created = StudentState.objects.update_or_create(
        student=student,
        academic_year=academic_year,
        defaults={
            'workflow_state': workflow_state,
            'final_april_state': final_april_state,
            'vetting_status': vetting_status,
        }
    )

    # Log the transition/initialization
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
            'legacy_override': bool(override if 'override' in locals() else False)
        }
    )

    return state
