from django.test import TestCase
from students.models import Student, AcademicResult
from school.models import Course, CourseOffering
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from students.services.auto_derivation import derive_student_state

class AutoDerivationTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            fiche=8001, full_name="Derive Test", permanent_code="DER80010001", level="Sec 1"
        )
        self.academic_year = "2025-2026"
        self.course1 = Course.objects.create(local_code="MAT101", description="Math", is_core_or_sanctioned=True)
        self.course2 = Course.objects.create(local_code="FRA101", description="French", is_core_or_sanctioned=True)
        self.offering1 = CourseOffering.objects.create(course=self.course1, group_number="01", academic_year=self.academic_year)
        self.offering2 = CourseOffering.objects.create(course=self.course2, group_number="01", academic_year=self.academic_year)

    def test_rule_1_auto_promote(self):
        """Rule 1: All core courses >= 60 -> READY_FOR_FINALIZATION / PROMOTE_REGULAR."""
        AcademicResult.objects.create(student=self.student, offering=self.offering1, academic_year=self.academic_year, final_grade=75)
        AcademicResult.objects.create(student=self.student, offering=self.offering2, academic_year=self.academic_year, final_grade=62)

        result = derive_student_state(self.student, self.academic_year)

        self.assertEqual(result["workflow_state"], WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(result["final_april_state"], FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR)
        self.assertEqual(result["vetting_status"], VettingStatus.AUTO_VETTED)

    def test_rule_2_teacher_review(self):
        """Rule 2: Grade 57-59 and no hard blockers -> REGULAR_REVIEW_PENDING."""
        AcademicResult.objects.create(student=self.student, offering=self.offering1, academic_year=self.academic_year, final_grade=58)
        AcademicResult.objects.create(student=self.student, offering=self.offering2, academic_year=self.academic_year, final_grade=80)

        result = derive_student_state(self.student, self.academic_year)

        self.assertEqual(result["workflow_state"], WorkflowState.REGULAR_REVIEW_PENDING)
        self.assertEqual(result["vetting_status"], VettingStatus.REQUIRES_REVIEW)
        self.assertIn("Teacher Review Needed", result["reason_codes"]["message"])

    def test_rule_3_summer_school(self):
        """Rule 3: Exactly one failure 50-59 (not in teacher review range) -> PROMOTE_WITH_SUMMER."""
        AcademicResult.objects.create(student=self.student, offering=self.offering1, academic_year=self.academic_year, final_grade=52)
        AcademicResult.objects.create(student=self.student, offering=self.offering2, academic_year=self.academic_year, final_grade=65)

        result = derive_student_state(self.student, self.academic_year)

        self.assertEqual(result["workflow_state"], WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(result["final_april_state"], FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER)

    def test_rule_4_ifp_candidate_multiple_fails(self):
        """Rule 4: >1 failure -> IFP_CANDIDATE_REVIEW."""
        AcademicResult.objects.create(student=self.student, offering=self.offering1, academic_year=self.academic_year, final_grade=55)
        AcademicResult.objects.create(student=self.student, offering=self.offering2, academic_year=self.academic_year, final_grade=58)

        result = derive_student_state(self.student, self.academic_year)

        self.assertEqual(result["workflow_state"], WorkflowState.IFP_CANDIDATE_REVIEW)

    def test_rule_4_ifp_candidate_hard_blocker(self):
        """Rule 4: Any hard blocker (< 50) -> IFP_CANDIDATE_REVIEW."""
        AcademicResult.objects.create(student=self.student, offering=self.offering1, academic_year=self.academic_year, final_grade=42)

        result = derive_student_state(self.student, self.academic_year)

        self.assertEqual(result["workflow_state"], WorkflowState.IFP_CANDIDATE_REVIEW)
        self.assertTrue(result["reason_codes"]["hard_blocker"])
