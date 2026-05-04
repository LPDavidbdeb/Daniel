from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from students.models import (
    Student, StudentState, StateTransitionLog, 
    AcademicResult, SummerSchoolEnrollment
)
from school.models import Course, CourseOffering
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from students.services.state_seeder import seed_student_state
from students.services.auto_derivation import derive_student_state
from students.services.state_engine import apply_event, close_april_snapshot, IllegalTransitionError, SnapshotClosureError
from students.constants import TEACHER_REVIEW_MIN

User = get_user_model()

class MasterIntegrationTest(TransactionTestCase):
    """
    Verifies the entire data lifecycle across Epic 1 and Epic 2.
    Ensures seeding, derivation, guards, and closure work as a cohesive unit.
    """

    def setUp(self):
        # Create a student and a core course
        self.student = Student.objects.create(
            fiche=10001, 
            full_name="Jean Tremblay", 
            permanent_code="TREJ10001001", 
            is_active=True
        )
        self.academic_year = "2025-2026"
        self.course = Course.objects.create(
            local_code="FRA101", 
            description="Français 1", 
            is_core_or_sanctioned=True
        )
        self.offering = CourseOffering.objects.create(
            course=self.course, 
            group_number="101", 
            academic_year=self.academic_year
        )
        self.user = User.objects.create(email="admin@gpi-optimizer.com")

    def test_complete_administrative_lifecycle(self):
        # --- Step 1: Legacy Data & Seeding (Epic 1) ---
        # Student has 55% in French (Summer School range, but too low for Teacher Review)
        result_obj = AcademicResult.objects.create(
            student=self.student, 
            offering=self.offering, 
            academic_year=self.academic_year, 
            final_grade=55
        )
        
        # Initial seeding
        seed_student_state(self.student, self.academic_year)
        
        # Assertions (US1.2, US1.3)
        state = StudentState.objects.get(student=self.student, academic_year=self.academic_year)
        self.assertEqual(state.workflow_state, WorkflowState.REGULAR_REVIEW_PENDING)
        self.assertEqual(state.vetting_status, VettingStatus.REQUIRES_REVIEW)
        
        logs = StateTransitionLog.objects.filter(student=self.student)
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs[0].event_name, "SYSTEM_SEED_INITIALIZATION")

        # --- Step 2: Auto-Derivation (Epic 2) ---
        derivation = derive_student_state(self.student, self.academic_year)
        
        # Assertions (US2.3)
        # 55% should suggest Summer School (Rule 3)
        self.assertEqual(derivation["workflow_state"], WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(derivation["final_april_state"], FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER)
        # New Micro/Macro architecture: message format updated
        self.assertIn("Summer", derivation["reason_codes"]["message"])

        # --- Step 3: Guard Rules Enforcement (Epic 2) ---
        # Attempt an illegal transition (promote regular despite 55% < 57% threshold)
        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                self.student, self.academic_year, "ILLEGAL_FORCE_PROMOTE",
                new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
                actor=self.user
            )
        self.assertIn("Teacher review override not permitted", str(cm.exception))
        
        # Verify no changes in ledger or audit trail for this event
        state.refresh_from_db()
        self.assertIsNone(state.final_april_state)
        self.assertEqual(StateTransitionLog.objects.filter(event_name="ILLEGAL_FORCE_PROMOTE").count(), 0)

        # --- Step 4: Snapshot Closure Gate (Epic 2) ---
        # Attempt to close the year while student is still REQUIRES_REVIEW
        # We need to ensure state is REQUIRES_REVIEW (seeding set it to that)
        with self.assertRaises(SnapshotClosureError):
            close_april_snapshot(self.academic_year)

        # --- Step 5: Resolution & Valid Transition (Epic 1 & 2) ---
        # Simulate teacher updating grade to 58 (legal for review override)
        result_obj.final_grade = 58
        result_obj.save()
        
        apply_event(
            self.student, self.academic_year, "MANUAL_TEACHER_REVIEW_PASS",
            new_workflow_state=WorkflowState.READY_FOR_FINALIZATION,
            new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
            new_vetting_status=VettingStatus.MANUALLY_VETTED,
            actor=self.user,
            payload={"note": "Reviewed and approved after grade adjustment."}
        )

        # Assertions (US2.1)
        state.refresh_from_db()
        self.assertEqual(state.workflow_state, WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR)
        self.assertEqual(state.vetting_status, VettingStatus.MANUALLY_VETTED)
        self.assertEqual(state.version, 2)
        
        logs = StateTransitionLog.objects.filter(student=self.student)
        self.assertEqual(logs.count(), 2)
        self.assertEqual(logs[0].event_name, "MANUAL_TEACHER_REVIEW_PASS") # Newest first

        # --- Step 6: Final Closure (Epic 2) ---
        result = close_april_snapshot(self.academic_year)
        self.assertTrue(result)
