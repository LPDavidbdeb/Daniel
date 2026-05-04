from django.test import TestCase
from django.db.utils import IntegrityError
from students.models import Student, StudentState
from students.enums import WorkflowState, FinalAprilState, VettingStatus

class StudentStateTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            fiche=1001,
            full_name="Alice Smith",
            permanent_code="SMIA10010001",
            level="Sec 3",
            current_group="301"
        )
        self.academic_year = "2025-2026"

    def test_create_student_state_valid(self):
        """Test creating a StudentState with minimal valid data."""
        state = StudentState.objects.create(
            student=self.student,
            academic_year=self.academic_year
        )
        self.assertEqual(state.student, self.student)
        self.assertEqual(state.academic_year, self.academic_year)
        self.assertEqual(state.version, 1)
        self.assertEqual(state.reason_codes, {})
        self.assertEqual(state.vetting_status, VettingStatus.REQUIRES_REVIEW) # Assuming REQUIRES_REVIEW is the logical default

    def test_unique_constraint(self):
        """Test that (student, academic_year) must be unique."""
        StudentState.objects.create(
            student=self.student,
            academic_year=self.academic_year
        )
        with self.assertRaises(IntegrityError):
            StudentState.objects.create(
                student=self.student,
                academic_year=self.academic_year
            )

    def test_full_fields_creation(self):
        """Test creating a StudentState with all fields."""
        state = StudentState.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            workflow_state=WorkflowState.READY_FOR_FINALIZATION,
            final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
            vetting_status=VettingStatus.AUTO_VETTED,
            ifp_target="N",
            reason_codes={"alert": "Low math score"},
            version=2
        )
        self.assertEqual(state.workflow_state, WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR)
        self.assertEqual(state.vetting_status, VettingStatus.AUTO_VETTED)
        self.assertEqual(state.ifp_target, "N")
        self.assertEqual(state.reason_codes, {"alert": "Low math score"})
        self.assertEqual(state.version, 2)
