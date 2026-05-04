from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from students.models import (
    Student, StudentState, StateTransitionLog, 
    SummerSchoolEnrollment, StudentPromotionOverride
)
from school.models import Course
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from students.services.state_seeder import seed_student_state

User = get_user_model()

class Epic1IntegrationTest(TestCase):
    def setUp(self):
        # Setup common data
        self.academic_year = "2025-2026"
        self.course = Course.objects.create(local_code="FRA101", description="Français")
        self.user = User.objects.create(email="coordinator@test.com")

    def test_end_to_end_seeding_and_audit(self):
        """
        Scenario: Legacy data exists for a student. Seeding command is run.
        Verify StudentState is correct and StateTransitionLog is created.
        """
        # Step 1: Create mock legacy data
        student = Student.objects.create(
            fiche=5001, 
            full_name="Integration Test Student", 
            permanent_code="INTA50010001", 
            is_active=True
        )
        
        # We simulate a student who has both an override and a summer enrollment.
        # According to mapping rules in US1.4, Summer Enrollment takes precedence.
        SummerSchoolEnrollment.objects.create(
            student=student, course=self.course, academic_year=self.academic_year
        )
        StudentPromotionOverride.objects.create(
            student=student, course=self.course, 
            academic_year=self.academic_year, override_type="FORCE_RETAKE"
        )

        # Step 2: Run seeding (invoking service directly to verify cohesive logic)
        seed_student_state(student, self.academic_year)

        # Step 3: Assertion - The Ledger
        state = StudentState.objects.get(student=student, academic_year=self.academic_year)
        # Summer enrollment precedence:
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER)
        self.assertEqual(state.vetting_status, VettingStatus.AUTO_VETTED)
        self.assertEqual(state.workflow_state, WorkflowState.REGULAR_REVIEW_PENDING)

        # Step 4: Assertion - The Audit
        log = StateTransitionLog.objects.filter(student=student).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.event_name, "SYSTEM_SEED_INITIALIZATION")
        self.assertEqual(log.to_state, WorkflowState.REGULAR_REVIEW_PENDING)
        self.assertIsNone(log.actor) # System event
        self.assertEqual(log.reason_payload['legacy_summer'], True)
        self.assertEqual(log.reason_payload['legacy_override'], True)

    def test_state_transition_and_audit_growth(self):
        """
        Scenario: An existing StudentState is updated.
        Verify the macro ledger updates and a new audit log entry is added.
        """
        student = Student.objects.create(
            fiche=5002, 
            full_name="Transition Test Student", 
            permanent_code="TRAA50020002", 
            is_active=True
        )
        
        # Initial seeding
        state = seed_student_state(student, self.academic_year)
        initial_log_count = StateTransitionLog.objects.filter(student=student).count()
        self.assertEqual(initial_log_count, 1)
        self.assertEqual(state.workflow_state, WorkflowState.REGULAR_REVIEW_PENDING)

        # Step 1: Change StudentState (simulating a service-layer state change)
        old_state_val = state.workflow_state
        new_state_val = WorkflowState.READY_FOR_FINALIZATION
        
        state.workflow_state = new_state_val
        state.vetting_status = VettingStatus.MANUALLY_VETTED
        state.version += 1
        state.save()

        # Step 2: Manually log the transition (as will be done by future transition services)
        StateTransitionLog.objects.create(
            student=student,
            from_state=old_state_val,
            to_state=new_state_val,
            event_name="MANUAL_COORDINATOR_REVIEW",
            actor=self.user,
            reason_payload={"note": "Verified student records manually."}
        )

        # Step 3: Assert macro ledger (StudentState) is updated
        updated_state = StudentState.objects.get(student=student, academic_year=self.academic_year)
        self.assertEqual(updated_state.workflow_state, WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(updated_state.vetting_status, VettingStatus.MANUALLY_VETTED)
        self.assertEqual(updated_state.version, 2)

        # Step 4: Assert audit trail grows while macro ledger stays singular
        logs = StateTransitionLog.objects.filter(student=student)
        self.assertEqual(logs.count(), 2)
        
        # Verify newest log (default ordering is -timestamp)
        latest_log = logs[0]
        self.assertEqual(latest_log.from_state, WorkflowState.REGULAR_REVIEW_PENDING)
        self.assertEqual(latest_log.to_state, WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(latest_log.actor, self.user)
        self.assertEqual(latest_log.event_name, "MANUAL_COORDINATOR_REVIEW")
        
        # Verify StudentState count for this year remains 1
        self.assertEqual(StudentState.objects.filter(student=student, academic_year=self.academic_year).count(), 1)
