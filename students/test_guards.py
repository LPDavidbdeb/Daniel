from django.test import TestCase
from students.models import Student, StudentState, AcademicResult
from school.models import Course, CourseOffering
from students.enums import WorkflowState, FinalAprilState
from students.services.state_engine import apply_event, IllegalTransitionError
from students.constants import PASS_THRESHOLD, FAIL_HARD_BLOCK_THRESHOLD, TEACHER_REVIEW_MIN, MAX_SUMMER_CLASSES

class GuardRulesTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            fiche=7001, full_name="Guard Test", permanent_code="GUA70010001", level="Sec 4"
        )
        self.academic_year = "2025-2026"
        self.state = StudentState.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            workflow_state=WorkflowState.REGULAR_REVIEW_PENDING
        )
        self.course1 = Course.objects.create(local_code="MAT401", description="Math", is_core_or_sanctioned=True)
        self.course2 = Course.objects.create(local_code="FRA401", description="French", is_core_or_sanctioned=True)
        self.offering1 = CourseOffering.objects.create(course=self.course1, group_number="01", academic_year=self.academic_year)
        self.offering2 = CourseOffering.objects.create(course=self.course2, group_number="01", academic_year=self.academic_year)

    def test_summer_limit_guard(self):
        """Cannot promote with summer if > 1 failed course in summer range."""
        AcademicResult.objects.create(student=self.student, offering=self.offering1, academic_year=self.academic_year, final_grade=55)
        AcademicResult.objects.create(student=self.student, offering=self.offering2, academic_year=self.academic_year, final_grade=55)

        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                self.student, self.academic_year, "ROUTE_TO_SUMMER",
                new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER
            )
        self.assertIn("maximum of 1 summer class", str(cm.exception))

    def test_hard_blocker_guard(self):
        """Core course < 50 makes student ineligible for summer promotion."""
        AcademicResult.objects.create(student=self.student, offering=self.offering1, academic_year=self.academic_year, final_grade=45)

        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                self.student, self.academic_year, "ROUTE_TO_SUMMER",
                new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER
            )
        self.assertIn("hard blocker", str(cm.exception))

    def test_summer_eligibility_guard_too_low(self):
        """Summer routing illegal if grade < 50."""
        AcademicResult.objects.create(student=self.student, offering=self.offering1, academic_year=self.academic_year, final_grade=49)
        
        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                self.student, self.academic_year, "ROUTE_TO_SUMMER",
                new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER
            )
        self.assertTrue("hard blocker" in str(cm.exception) or "ineligible" in str(cm.exception))

    def test_ifp_prerequisite_guard(self):
        """Cannot finalize to IFP unless workflow state was IFP_CANDIDATE_REVIEW."""
        # Current state is REGULAR_REVIEW_PENDING
        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                self.student, self.academic_year, "FINALIZE_IFP",
                new_final_april_state=FinalAprilState.APRIL_FINAL_IFP_N
            )
        self.assertIn("IFP_CANDIDATE_REVIEW", str(cm.exception))

        # Should work if moved to IFP_CANDIDATE_REVIEW first
        self.state.workflow_state = WorkflowState.IFP_CANDIDATE_REVIEW
        self.state.save()
        
        apply_event(
            self.student, self.academic_year, "FINALIZE_IFP",
            new_final_april_state=FinalAprilState.APRIL_FINAL_IFP_N
        )
        self.state.refresh_from_db()
        self.assertEqual(self.state.final_april_state, FinalAprilState.APRIL_FINAL_IFP_N)

    def test_teacher_review_boundary_pass(self):
        """Overriding to promote regular is only allowed if grades are >= 57."""
        AcademicResult.objects.create(student=self.student, offering=self.offering1, academic_year=self.academic_year, final_grade=56)

        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                self.student, self.academic_year, "TEACHER_REVIEW_OVERRIDE",
                new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR
            )
        self.assertIn("Teacher review", str(cm.exception))

        # Should work if grade is 57
        AcademicResult.objects.filter(student=self.student).update(final_grade=57)
        apply_event(
            self.student, self.academic_year, "TEACHER_REVIEW_OVERRIDE",
            new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR
        )
        self.state.refresh_from_db()
        self.assertEqual(self.state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR)
