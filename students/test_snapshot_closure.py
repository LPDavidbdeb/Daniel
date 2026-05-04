from django.test import TestCase
from students.models import Student, StudentState
from students.enums import VettingStatus
from students.services.state_engine import close_april_snapshot, SnapshotClosureError

class SnapshotClosureTest(TestCase):
    def setUp(self):
        self.academic_year = "2025-2026"
        # Create finalized active students
        for i in range(5):
            student = Student.objects.create(
                fiche=9000+i, full_name=f"Vetted Student {i}", 
                permanent_code=f"VET{9000+i}", is_active=True
            )
            StudentState.objects.create(
                student=student, academic_year=self.academic_year, 
                vetting_status=VettingStatus.AUTO_VETTED
            )

    def test_closure_failure_with_unvetted_student(self):
        """Gate should block closure if 1 active student is REQUIRES_REVIEW."""
        unvetted_student = Student.objects.create(
            fiche=9100, full_name="Unvetted Student", 
            permanent_code="UNV9100", is_active=True
        )
        StudentState.objects.create(
            student=unvetted_student, academic_year=self.academic_year, 
            vetting_status=VettingStatus.REQUIRES_REVIEW
        )

        with self.assertRaises(SnapshotClosureError) as cm:
            close_april_snapshot(self.academic_year)
        
        self.assertIn("Unvetted Student", str(cm.exception))
        self.assertEqual(cm.exception.incomplete_students[0]['fiche'], 9100)

    def test_closure_success_all_vetted(self):
        """Gate should allow closure if 100% of active students are finalized."""
        # Setup already created 5 vetted students
        result = close_april_snapshot(self.academic_year)
        self.assertTrue(result)

    def test_closure_ignores_inactive_students(self):
        """Gate should ignore inactive students even if they are REQUIRES_REVIEW."""
        inactive_student = Student.objects.create(
            fiche=9200, full_name="Inactive Student", 
            permanent_code="INA9200", is_active=False
        )
        StudentState.objects.create(
            student=inactive_student, academic_year=self.academic_year, 
            vetting_status=VettingStatus.REQUIRES_REVIEW
        )

        # All 5 active students are vetted, so this should pass
        result = close_april_snapshot(self.academic_year)
        self.assertTrue(result)
