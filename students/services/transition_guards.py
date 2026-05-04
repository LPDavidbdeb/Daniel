from students.models import Student, StudentState, AcademicResult
from students.enums import WorkflowState, FinalAprilState
from students.constants import PASS_THRESHOLD, FAIL_HARD_BLOCK_THRESHOLD, TEACHER_REVIEW_MIN, MAX_SUMMER_CLASSES
from django.db.models import Q

def validate_transition(
    student: Student,
    academic_year: str,
    from_workflow_state: str,
    new_workflow_state: str = None,
    new_final_april_state: str = None,
):
    """
    Validates a student's state transition against pedagogical invariants.
    Raises IllegalTransitionError if a rule is violated.
    """
    from students.services.state_engine import IllegalTransitionError

    # Rule: IFP Prerequisites
    # A student cannot be finalized to APRIL_FINAL_IFP_N or APRIL_FINAL_IFP_N_MINUS_1
    # unless they have a preceding workflow state indicating they were an IFP candidate.
    if new_final_april_state in [FinalAprilState.APRIL_FINAL_IFP_N, FinalAprilState.APRIL_FINAL_IFP_N_MINUS_1]:
        if from_workflow_state != WorkflowState.IFP_CANDIDATE_REVIEW:
            raise IllegalTransitionError(
                f"Student must be in {WorkflowState.IFP_CANDIDATE_REVIEW} to be finalized as an IFP candidate."
            )

    # Fetch results for rules involving grades
    results = AcademicResult.objects.filter(
        student=student, 
        academic_year=academic_year
    ).select_related('offering__course')

    # Rule: Summer Eligibility and Hard Blockers
    if new_final_april_state == FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER:
        failed_courses_in_summer_range = 0
        
        for res in results:
            if res.final_grade is not None and res.final_grade < PASS_THRESHOLD:
                # Rule: Hard Blocker
                # Any core/sanctioned course grade < 50 is a hard blocker.
                if res.offering.course.is_core_or_sanctioned and res.final_grade < FAIL_HARD_BLOCK_THRESHOLD:
                    raise IllegalTransitionError(
                        f"Course {res.offering.course.local_code} is a hard blocker (grade < {FAIL_HARD_BLOCK_THRESHOLD})."
                    )
                
                # Rule: Summer Eligibility
                # Summer school routing is only permitted if the failed course grade is between 50 and 59.
                if res.final_grade < FAIL_HARD_BLOCK_THRESHOLD:
                     raise IllegalTransitionError(
                        f"Student is ineligible for summer school due to grade {res.final_grade} in {res.offering.course.local_code}."
                    )
                
                if FAIL_HARD_BLOCK_THRESHOLD <= res.final_grade < PASS_THRESHOLD:
                    failed_courses_in_summer_range += 1

        # Rule: Summer Limit
        # A student can be assigned a maximum of 1 summer class per year.
        if failed_courses_in_summer_range > MAX_SUMMER_CLASSES:
             raise IllegalTransitionError(
                f"Student exceeds maximum of {MAX_SUMMER_CLASSES} summer class(es) (has {failed_courses_in_summer_range})."
            )

    # Rule: Teacher Review Boundary
    # A teacher review action (e.g., overriding a fail to a pass) is only permitted if the course grade is between 57 and 59.
    if new_final_april_state == FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR:
        for res in results:
            if res.final_grade is not None and res.final_grade < PASS_THRESHOLD:
                if res.final_grade < TEACHER_REVIEW_MIN:
                     raise IllegalTransitionError(
                        f"Teacher review override not permitted for grade {res.final_grade} in {res.offering.course.local_code} (min {TEACHER_REVIEW_MIN})."
                    )
