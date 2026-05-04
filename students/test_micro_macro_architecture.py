"""
Test Suite for Micro/Macro Architecture - Two-Level State Derivation

This test suite validates the new two-level architecture for derive_student_state:
- LEVEL 1 (MICRO): Evaluates each course individually
- LEVEL 2 (MACRO): Aggregates micro results with strict hierarchical precedence
"""

from django.test import TestCase
from students.models import Student, AcademicResult
from school.models import Course, CourseOffering, Teacher
from students.enums import (
    WorkflowState,
    FinalAprilState,
    VettingStatus,
    CourseEvalState,
)
from students.services.auto_derivation import (
    derive_student_state,
    evaluate_course_result,
    aggregate_micro_results,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class MicroLevelEvaluationTest(TestCase):
    """Tests for Micro-level (individual course) evaluation."""

    def setUp(self):
        self.student = Student.objects.create(
            fiche=9001,
            full_name="Micro Test",
            permanent_code="MIC90010001"
        )
        self.academic_year = "2025-2026"
        self.teacher = Teacher.objects.create(full_name="Prof Micro")

    def _create_course_and_result(self, local_code: str, grade: int, is_core: bool = True) -> AcademicResult:
        """Helper to create a course, offering, and result."""
        course = Course.objects.create(
            local_code=local_code,
            description=f"Course {local_code}",
            is_core_or_sanctioned=is_core
        )
        offering = CourseOffering.objects.create(
            course=course,
            group_number="01",
            academic_year=self.academic_year,
            teacher=self.teacher
        )
        result = AcademicResult.objects.create(
            student=self.student,
            offering=offering,
            academic_year=self.academic_year,
            final_grade=grade
        )
        return result

    def test_micro_pass_grade(self):
        """Micro: Grade >= 60 → PASS"""
        result = self._create_course_and_result("FRA101", 75)
        state, reason = evaluate_course_result(result)
        self.assertEqual(state, CourseEvalState.PASS)
        self.assertIn("75", reason)

    def test_micro_teacher_review_57(self):
        """Micro: Grade 57 → TEACHER_REVIEW_PENDING"""
        result = self._create_course_and_result("MAT101", 57)
        state, reason = evaluate_course_result(result)
        self.assertEqual(state, CourseEvalState.TEACHER_REVIEW_PENDING)
        self.assertIn("57", reason)

    def test_micro_teacher_review_59(self):
        """Micro: Grade 59 → TEACHER_REVIEW_PENDING"""
        result = self._create_course_and_result("FRA101", 59)
        state, reason = evaluate_course_result(result)
        self.assertEqual(state, CourseEvalState.TEACHER_REVIEW_PENDING)
        self.assertIn("59", reason)

    def test_micro_summer_eligible_core_course(self):
        """Micro: Grade 50-56 on core course → SUMMER_ELIGIBLE"""
        result = self._create_course_and_result("MAT101", 52, is_core=True)
        state, reason = evaluate_course_result(result)
        self.assertEqual(state, CourseEvalState.SUMMER_ELIGIBLE)

    def test_micro_summer_eligible_boundary_50(self):
        """Micro: Grade exactly 50 on core course → SUMMER_ELIGIBLE"""
        result = self._create_course_and_result("MAT101", 50, is_core=True)
        state, reason = evaluate_course_result(result)
        self.assertEqual(state, CourseEvalState.SUMMER_ELIGIBLE)

    def test_micro_summer_eligible_boundary_56(self):
        """Micro: Grade exactly 56 on core course → SUMMER_ELIGIBLE"""
        result = self._create_course_and_result("MAT101", 56, is_core=True)
        state, reason = evaluate_course_result(result)
        self.assertEqual(state, CourseEvalState.SUMMER_ELIGIBLE)

    def test_micro_failed_non_core_50_to_56(self):
        """Micro: Grade 50-56 on non-core course → FAILED"""
        result = self._create_course_and_result("OPT101", 52, is_core=False)
        state, reason = evaluate_course_result(result)
        self.assertEqual(state, CourseEvalState.FAILED)

    def test_micro_failed_hard_blocker(self):
        """Micro: Grade < 50 → FAILED (hard blocker)"""
        result = self._create_course_and_result("FRA101", 42)
        state, reason = evaluate_course_result(result)
        self.assertEqual(state, CourseEvalState.FAILED)

    def test_micro_failed_at_49(self):
        """Micro: Grade 49 → FAILED (just below 50)"""
        result = self._create_course_and_result("MAT101", 49)
        state, reason = evaluate_course_result(result)
        self.assertEqual(state, CourseEvalState.FAILED)


class MacroLevelAggregationTest(TestCase):
    """Tests for Macro-level (student-year) aggregation."""

    def test_macro_rule1_absolute_priority_teacher_review(self):
        """
        Macro Rule 1 (Absolute Priority): If ANY course is TEACHER_REVIEW_PENDING
        → REGULAR_REVIEW_PENDING with REQUIRES_REVIEW
        """
        micro_states = {
            "FRA228": CourseEvalState.TEACHER_REVIEW_PENDING,
            "MAT101": CourseEvalState.PASS,
        }
        reason_codes_by_state = {
            CourseEvalState.PASS: ["MAT101 (75%)"],
            CourseEvalState.TEACHER_REVIEW_PENDING: ["FRA228 (57%)"],
            CourseEvalState.SUMMER_ELIGIBLE: [],
            CourseEvalState.FAILED: [],
        }

        workflow_state, final_state, vetting, payload = aggregate_micro_results(
            micro_states, reason_codes_by_state
        )

        self.assertEqual(workflow_state, WorkflowState.REGULAR_REVIEW_PENDING)
        self.assertIsNone(final_state)
        self.assertEqual(vetting, VettingStatus.REQUIRES_REVIEW)
        self.assertEqual(payload["rule"], "TEACHER_REVIEW_PRIORITY")
        self.assertIn("FRA228 (57%)", payload["teacher_review_courses"])

    def test_macro_rule2_secondary_priority_summer_routing(self):
        """
        Macro Rule 2 (Secondary Priority): No teacher review, but ANY SUMMER_ELIGIBLE
        → READY_FOR_FINALIZATION with APRIL_FINAL_PROMOTE_WITH_SUMMER
        """
        micro_states = {
            "MAT101": CourseEvalState.SUMMER_ELIGIBLE,
            "FRA101": CourseEvalState.PASS,
        }
        reason_codes_by_state = {
            CourseEvalState.PASS: ["FRA101 (65%)"],
            CourseEvalState.TEACHER_REVIEW_PENDING: [],
            CourseEvalState.SUMMER_ELIGIBLE: ["MAT101 (52%)"],
            CourseEvalState.FAILED: [],
        }

        workflow_state, final_state, vetting, payload = aggregate_micro_results(
            micro_states, reason_codes_by_state
        )

        self.assertEqual(workflow_state, WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(final_state, FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER)
        self.assertEqual(vetting, VettingStatus.AUTO_VETTED)
        self.assertEqual(payload["rule"], "SUMMER_ROUTING")

    def test_macro_rule3_all_pass(self):
        """Macro Rule 3: All courses PASS → PROMOTE_REGULAR"""
        micro_states = {
            "FRA101": CourseEvalState.PASS,
            "MAT101": CourseEvalState.PASS,
        }
        reason_codes_by_state = {
            CourseEvalState.PASS: ["FRA101 (75%)", "MAT101 (80%)"],
            CourseEvalState.TEACHER_REVIEW_PENDING: [],
            CourseEvalState.SUMMER_ELIGIBLE: [],
            CourseEvalState.FAILED: [],
        }

        workflow_state, final_state, vetting, payload = aggregate_micro_results(
            micro_states, reason_codes_by_state
        )

        self.assertEqual(workflow_state, WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(final_state, FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR)
        self.assertEqual(vetting, VettingStatus.AUTO_VETTED)
        self.assertEqual(payload["rule"], "AUTO_PROMOTE")

    def test_macro_rule4_hard_failure(self):
        """Macro Rule 4: ANY FAILED course → IFP_CANDIDATE_REVIEW"""
        micro_states = {
            "FRA101": CourseEvalState.FAILED,
            "MAT101": CourseEvalState.PASS,
        }
        reason_codes_by_state = {
            CourseEvalState.PASS: ["MAT101 (65%)"],
            CourseEvalState.TEACHER_REVIEW_PENDING: [],
            CourseEvalState.SUMMER_ELIGIBLE: [],
            CourseEvalState.FAILED: ["FRA101 (42%)"],
        }

        workflow_state, final_state, vetting, payload = aggregate_micro_results(
            micro_states, reason_codes_by_state
        )

        self.assertEqual(workflow_state, WorkflowState.IFP_CANDIDATE_REVIEW)
        self.assertIsNone(final_state)
        self.assertEqual(vetting, VettingStatus.REQUIRES_REVIEW)
        self.assertEqual(payload["rule"], "HARD_FAILURE")


class IntegrationTestAhmedChabane(TestCase):
    """
    CRITICAL TEST: Ahmed Chabane case
    - FRA228: 57% (Teacher Review PENDING)
    - CCQ222: 59% (Teacher Review PENDING)

    Expected: REGULAR_REVIEW_PENDING with both courses listed
    """

    def setUp(self):
        self.student = Student.objects.create(
            fiche=8002,
            full_name="Ahmed Chabane",
            permanent_code="ACH80020001",
            level="Sec 3"
        )
        self.academic_year = "2025-2026"
        self.teacher = Teacher.objects.create(full_name="Prof Principal")

    def test_ahmed_chabane_two_teacher_reviews(self):
        """
        Test Case: Ahmed Chabane
        - FRA228 (57%) → TEACHER_REVIEW_PENDING
        - CCQ222 (59%) → TEACHER_REVIEW_PENDING

        Expected Result:
        - workflow_state: REGULAR_REVIEW_PENDING
        - vetting_status: REQUIRES_REVIEW
        - reason_codes includes both courses
        """
        # Create courses
        fra228 = Course.objects.create(
            local_code="FRA228",
            description="Français",
            is_core_or_sanctioned=True
        )
        ccq222 = Course.objects.create(
            local_code="CCQ222",
            description="Chimie",
            is_core_or_sanctioned=True
        )

        # Create offerings
        fra_offering = CourseOffering.objects.create(
            course=fra228,
            group_number="01",
            academic_year=self.academic_year,
            teacher=self.teacher
        )
        ccq_offering = CourseOffering.objects.create(
            course=ccq222,
            group_number="01",
            academic_year=self.academic_year,
            teacher=self.teacher
        )

        # Create results
        AcademicResult.objects.create(
            student=self.student,
            offering=fra_offering,
            academic_year=self.academic_year,
            final_grade=57
        )
        AcademicResult.objects.create(
            student=self.student,
            offering=ccq_offering,
            academic_year=self.academic_year,
            final_grade=59
        )

        # Derive state
        result = derive_student_state(self.student, self.academic_year)

        # Assertions
        self.assertEqual(
            result["workflow_state"],
            WorkflowState.REGULAR_REVIEW_PENDING,
            "Ahmed should be in REGULAR_REVIEW_PENDING (Teacher Review Priority)"
        )
        self.assertIsNone(
            result["final_april_state"],
            "No final state should be assigned during review"
        )
        self.assertEqual(
            result["vetting_status"],
            VettingStatus.REQUIRES_REVIEW,
            "Status should be REQUIRES_REVIEW"
        )

        # Verify both courses are listed in reason_codes
        reason_codes = result["reason_codes"]
        teacher_review_courses = reason_codes.get("teacher_review_courses", [])
        self.assertIn(
            "FRA228 (57%)",
            teacher_review_courses,
            "FRA228 (57%) should be listed in teacher_review_courses"
        )
        self.assertIn(
            "CCQ222 (59%)",
            teacher_review_courses,
            "CCQ222 (59%) should be listed in teacher_review_courses"
        )
        self.assertEqual(
            len(teacher_review_courses),
            2,
            "Exactly 2 teacher review courses should be listed"
        )
        self.assertEqual(
            reason_codes["rule"],
            "TEACHER_REVIEW_PRIORITY",
            "Rule should be TEACHER_REVIEW_PRIORITY"
        )


class PrecedenceTestMathAndFrench(TestCase):
    """
    PRECEDENCE TEST: Teacher Review > Summer School Decision

    Scenario:
    - Math (52%) on core course → SUMMER_ELIGIBLE
    - Français (58%) → TEACHER_REVIEW_PENDING

    Expected: REGULAR_REVIEW_PENDING (Teacher Review takes absolute priority)
    - Summer school decision for Math is suspended pending French teacher review
    """

    def setUp(self):
        self.student = Student.objects.create(
            fiche=8003,
            full_name="Precedence Test",
            permanent_code="PRE80030001"
        )
        self.academic_year = "2025-2026"
        self.teacher = Teacher.objects.create(full_name="Prof Test")

    def test_precedence_teacher_review_blocks_summer(self):
        """Teacher Review decision suspends summer school routing."""
        # Create courses
        math = Course.objects.create(
            local_code="MAT101",
            description="Mathématiques",
            is_core_or_sanctioned=True
        )
        french = Course.objects.create(
            local_code="FRA101",
            description="Français",
            is_core_or_sanctioned=True
        )

        # Create offerings
        math_offering = CourseOffering.objects.create(
            course=math,
            group_number="01",
            academic_year=self.academic_year,
            teacher=self.teacher
        )
        french_offering = CourseOffering.objects.create(
            course=french,
            group_number="01",
            academic_year=self.academic_year,
            teacher=self.teacher
        )

        # Create results
        AcademicResult.objects.create(
            student=self.student,
            offering=math_offering,
            academic_year=self.academic_year,
            final_grade=52  # Summer eligible
        )
        AcademicResult.objects.create(
            student=self.student,
            offering=french_offering,
            academic_year=self.academic_year,
            final_grade=58  # Teacher review
        )

        # Derive state
        result = derive_student_state(self.student, self.academic_year)

        # Assertions
        self.assertEqual(
            result["workflow_state"],
            WorkflowState.REGULAR_REVIEW_PENDING,
            "Should be in REGULAR_REVIEW_PENDING (Teacher Review > Summer)"
        )

        # Verify reason codes
        reason_codes = result["reason_codes"]
        self.assertEqual(
            reason_codes["rule"],
            "TEACHER_REVIEW_PRIORITY",
            "Rule should reflect Teacher Review Priority"
        )
        self.assertIn(
            "FRA101 (58%)",
            reason_codes["teacher_review_courses"]
        )


class NoShortCircuitTest(TestCase):
    """
    Test that ALL courses are evaluated (no short-circuiting on first failure).

    This validates the core architectural change:
    - Old: Short-circuit on first failure
    - New: Loop through ALL courses before aggregating
    """

    def setUp(self):
        self.student = Student.objects.create(
            fiche=8004,
            full_name="No Short Circuit",
            permanent_code="NSC80040001"
        )
        self.academic_year = "2025-2026"
        self.teacher = Teacher.objects.create(full_name="Prof Test")

    def test_all_courses_evaluated_multiple_failures(self):
        """Verify ALL failures are captured, not just first."""
        courses_and_grades = [
            ("FRA101", 45),    # FAILED (hard blocker)
            ("MAT101", 52),    # SUMMER_ELIGIBLE
            ("ANG101", 58),    # TEACHER_REVIEW_PENDING
            ("PHY101", 49),    # FAILED (hard blocker)
        ]

        for code, grade in courses_and_grades:
            course = Course.objects.create(
                local_code=code,
                description=f"Course {code}",
                is_core_or_sanctioned=True
            )
            offering = CourseOffering.objects.create(
                course=course,
                group_number="01",
                academic_year=self.academic_year,
                teacher=self.teacher
            )
            AcademicResult.objects.create(
                student=self.student,
                offering=offering,
                academic_year=self.academic_year,
                final_grade=grade
            )

        result = derive_student_state(self.student, self.academic_year)

        # Because we have TEACHER_REVIEW_PENDING (ANG101: 58%), that takes priority
        self.assertEqual(
            result["workflow_state"],
            WorkflowState.REGULAR_REVIEW_PENDING
        )

        # Verify micro analysis includes all courses
        micro_analysis = result["reason_codes"].get("micro_analysis", {})
        courses_evaluated = micro_analysis.get("courses_evaluated", [])
        self.assertEqual(len(courses_evaluated), 4, "All 4 courses should be evaluated")

        # Verify state distribution shows all types
        state_dist = micro_analysis.get("state_distribution", {})
        self.assertGreater(
            len(state_dist),
            1,
            "Multiple course states should be represented"
        )

