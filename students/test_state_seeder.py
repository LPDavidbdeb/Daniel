from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from students.models import (
    Student, StudentState, StateTransitionLog, 
    SummerSchoolEnrollment, StudentPromotionOverride
)
from school.models import Course
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from students.services.state_seeder import seed_student_state

class StateSeederServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            fiche=3001, full_name="Alice Seeder", permanent_code="SEEA30010001", is_active=True
        )
        self.academic_year = "2025-2026"
        self.course = Course.objects.create(local_code="MAT101", description="Math")

    def test_seed_new_student_no_legacy(self):
        """Student with no legacy data should get REQUIRES_REVIEW and a pending workflow state."""
        seed_student_state(self.student, self.academic_year)
        
        state = StudentState.objects.get(student=self.student, academic_year=self.academic_year)
        self.assertEqual(state.vetting_status, VettingStatus.REQUIRES_REVIEW)
        self.assertEqual(state.workflow_state, WorkflowState.REGULAR_REVIEW_PENDING)
        self.assertIsNone(state.final_april_state)
        
        # Check audit log
        log = StateTransitionLog.objects.get(student=self.student)
        self.assertEqual(log.event_name, "SYSTEM_SEED_INITIALIZATION")
        self.assertEqual(log.to_state, WorkflowState.REGULAR_REVIEW_PENDING)

    def test_seed_with_summer_school(self):
        """Student with summer school enrollment should map to PROMOTE_WITH_SUMMER."""
        SummerSchoolEnrollment.objects.create(
            student=self.student, course=self.course, academic_year=self.academic_year
        )
        seed_student_state(self.student, self.academic_year)
        
        state = StudentState.objects.get(student=self.student, academic_year=self.academic_year)
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER)
        self.assertEqual(state.vetting_status, VettingStatus.AUTO_VETTED)

    def test_seed_with_override(self):
        """Student with override should map to corresponding FinalAprilState."""
        StudentPromotionOverride.objects.create(
            student=self.student, course=self.course, 
            academic_year=self.academic_year, override_type="FORCE_PASS"
        )
        seed_student_state(self.student, self.academic_year)
        
        state = StudentState.objects.get(student=self.student, academic_year=self.academic_year)
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR)

class StateSeederCommandTest(TestCase):
    def setUp(self):
        self.active_student = Student.objects.create(
            fiche=4001, full_name="Active Stu", permanent_code="ACTA40010001", is_active=True
        )
        self.inactive_student = Student.objects.create(
            fiche=4002, full_name="Inactive Stu", permanent_code="INAA40020002", is_active=False
        )
        self.academic_year = "2025-2026"

    def test_command_processes_only_active_students(self):
        out = StringIO()
        call_command("seed_student_states", year=self.academic_year, stdout=out)
        
        self.assertTrue(StudentState.objects.filter(student=self.active_student).exists())
        self.assertFalse(StudentState.objects.filter(student=self.inactive_student).exists())
        self.assertIn("Successfully seeded 1 student states", out.getvalue())

    def test_command_idempotency(self):
        """Running the command twice should not create duplicate states or fail."""
        call_command("seed_student_states", year=self.academic_year)
        count1 = StudentState.objects.count()
        
        call_command("seed_student_states", year=self.academic_year)
        count2 = StudentState.objects.count()
        
        self.assertEqual(count1, count2)
        self.assertEqual(count1, 1)
