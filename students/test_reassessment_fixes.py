"""
TDD Test Suite: Re-Assessment Fixes for Epics 1 & 2
Tests for all 17 identified issues, in priority order.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from students.models import (
    Student, StudentState, StateTransitionLog,
    AcademicResult, StudentPromotionOverride
)
from school.models import Course, CourseOffering
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from students.services.state_engine import apply_event, IllegalTransitionError, close_april_snapshot, SnapshotClosureError
from students.services.auto_derivation import derive_student_state
from students.services.state_seeder import seed_student_state

User = get_user_model()


# ============================================================================
# CRITICAL ISSUES
# ============================================================================

class TestUS23ZeroGradeAutoPromote(TestCase):
    """US2.3: Student with no grades (all final_grade=None) should NOT auto-promote."""

    def setUp(self):
        self.student = Student.objects.create(
            fiche=1001, full_name="No Grades Student",
            permanent_code="NOGRD1001001", is_active=True
        )
        self.academic_year = "2025-2026"
        self.course = Course.objects.create(
            local_code="MAT401", description="Math 4", is_core_or_sanctioned=True
        )
        self.offering = CourseOffering.objects.create(
            course=self.course, group_number="401", academic_year=self.academic_year
        )

    def test_student_with_no_academic_results_requires_review(self):
        """No AcademicResult rows → REQUIRES_REVIEW, not auto-promote."""
        result = derive_student_state(self.student, self.academic_year)
        self.assertEqual(result["vetting_status"], VettingStatus.REQUIRES_REVIEW)
        self.assertIn("MISSING_GRADES", result["reason_codes"].get("message", ""))

    def test_student_with_all_none_grades_requires_review(self):
        """All core courses have final_grade=None → REQUIRES_REVIEW, not auto-promote."""
        AcademicResult.objects.create(
            student=self.student, offering=self.offering,
            academic_year=self.academic_year, final_grade=None
        )
        result = derive_student_state(self.student, self.academic_year)
        self.assertEqual(result["vetting_status"], VettingStatus.REQUIRES_REVIEW)
        self.assertIn("MISSING_GRADES", result["reason_codes"].get("message", ""))


class TestUS14TransferIFPWorkflowMapping(TestCase):
    """US1.4: TRANSFER_IFP seeder must set workflow_state=IFP_CANDIDATE_REVIEW, not REGULAR_REVIEW_PENDING."""

    def setUp(self):
        self.student = Student.objects.create(
            fiche=1002, full_name="Transfer IFP Student",
            permanent_code="XIFP1002001", is_active=True
        )
        self.academic_year = "2025-2026"
        self.course = Course.objects.create(
            local_code="DUM401", description="Dummy", is_core_or_sanctioned=True
        )
        self.override = StudentPromotionOverride.objects.create(
            student=self.student, academic_year=self.academic_year,
            course=self.course,
            override_type="TRANSFER_IFP"
        )

    def test_seeder_transfer_ifp_sets_ifp_candidate_workflow(self):
        """TRANSFER_IFP override → workflow_state=IFP_CANDIDATE_REVIEW."""
        state = seed_student_state(self.student, self.academic_year)
        self.assertEqual(state.workflow_state, WorkflowState.IFP_CANDIDATE_REVIEW)
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_IFP_N)
        self.assertEqual(state.vetting_status, VettingStatus.AUTO_VETTED)

    def test_seeder_transfer_dim_sets_ifp_candidate_workflow(self):
        """TRANSFER_DIM override → workflow_state=IFP_CANDIDATE_REVIEW."""
        self.override.override_type = "TRANSFER_DIM"
        self.override.save()
        state = seed_student_state(self.student, self.academic_year)
        self.assertEqual(state.workflow_state, WorkflowState.IFP_CANDIDATE_REVIEW)
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_HOLDBACK)


class TestUS24InvisibleStudentsInSnapshot(TestCase):
    """US2.4: Active student with no StudentState row must block snapshot closure."""

    def setUp(self):
        self.academic_year = "2025-2026"

    def test_active_student_without_state_row_blocks_snapshot(self):
        """Active student with no StudentState → snapshot closure should fail."""
        student = Student.objects.create(
            fiche=1003, full_name="Invisible Student",
            permanent_code="INVS1003001", is_active=True
        )

        with self.assertRaises(SnapshotClosureError) as cm:
            close_april_snapshot(self.academic_year)

        self.assertIn("Invisible Student", str(cm.exception))


class TestNewCourseDoesNotExistInSummerSync(TransactionTestCase):
    """NEW: Course.objects.get(id=bad_id) in summer sync crashes state transition."""

    def setUp(self):
        self.student = Student.objects.create(
            fiche=1004, full_name="Summer Student",
            permanent_code="SUMM1004001", is_active=True
        )
        self.academic_year = "2025-2026"
        self.user = User.objects.create(email="test@test.com")

        StudentState.objects.create(
            student=self.student, academic_year=self.academic_year,
            workflow_state=WorkflowState.REGULAR_REVIEW_PENDING,
            vetting_status=VettingStatus.REQUIRES_REVIEW
        )

    def test_bad_course_id_raises_illegal_transition_error(self):
        """Invalid course_id in payload → IllegalTransitionError, not DoesNotExist."""
        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                student=self.student, academic_year=self.academic_year,
                event_name="ASSIGN_SUMMER",
                new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER,
                actor=self.user,
                payload={"course_id": 99999}
            )

        self.assertIn("course", str(cm.exception).lower())


class TestUS21StudentStateDoesNotExistHandled(TransactionTestCase):
    """US2.1: StudentState.DoesNotExist from .get() must raise IllegalTransitionError."""

    def setUp(self):
        self.student = Student.objects.create(
            fiche=1005, full_name="Unseeded Student",
            permanent_code="UNSD1005001", is_active=True
        )
        self.academic_year = "2025-2026"
        self.user = User.objects.create(email="test2@test.com")

    def test_apply_event_unseeded_student_raises_illegal_transition(self):
        """apply_event on unseeded student → IllegalTransitionError, not DoesNotExist crash."""
        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                student=self.student, academic_year=self.academic_year,
                event_name="MANUAL_REVIEW",
                new_workflow_state=WorkflowState.REGULAR_REVIEW_PENDING,
                actor=self.user
            )

        self.assertIn("not seeded", str(cm.exception).lower())


class TestUS22HoldbackGuard(TestCase):
    """US2.2: No guard on APRIL_FINAL_HOLDBACK — must validate grades."""

    def setUp(self):
        self.student = Student.objects.create(
            fiche=1006, full_name="Holdback Test",
            permanent_code="HOLD1006001", is_active=True
        )
        self.academic_year = "2025-2026"
        self.user = User.objects.create(email="test3@test.com")

        StudentState.objects.create(
            student=self.student, academic_year=self.academic_year,
            workflow_state=WorkflowState.REGULAR_REVIEW_PENDING,
            vetting_status=VettingStatus.REQUIRES_REVIEW
        )

    def test_holdback_requires_at_least_one_failure(self):
        """Cannot assign HOLDBACK without failed courses."""
        course = Course.objects.create(
            local_code="ENG401", description="English 4", is_core_or_sanctioned=True
        )
        offering = CourseOffering.objects.create(
            course=course, group_number="401", academic_year=self.academic_year
        )
        AcademicResult.objects.create(
            student=self.student, offering=offering,
            academic_year=self.academic_year, final_grade=75
        )

        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                student=self.student, academic_year=self.academic_year,
                event_name="MANUAL_HOLDBACK",
                new_final_april_state=FinalAprilState.APRIL_FINAL_HOLDBACK,
                actor=self.user
            )

        self.assertIn("holdback", str(cm.exception).lower())


# ============================================================================
# HIGH PRIORITY ISSUES
# ============================================================================

class TestUS12ReasonCodesPeristence(TestCase):
    """US1.2: reason_codes field must be written and persisted."""

    def setUp(self):
        self.student = Student.objects.create(
            fiche=1007, full_name="Reason Codes Student",
            permanent_code="RSCD1007001", is_active=True
        )
        self.academic_year = "2025-2026"
        self.user = User.objects.create(email="test4@test.com")

        StudentState.objects.create(
            student=self.student, academic_year=self.academic_year,
            workflow_state=WorkflowState.REGULAR_REVIEW_PENDING,
            vetting_status=VettingStatus.REQUIRES_REVIEW
        )

    def test_apply_event_persists_reason_codes_to_student_state(self):
        """apply_event with new_reason_codes must persist to StudentState."""
        test_codes = {"message": "Manual override", "actor": "principal"}

        apply_event(
            student=self.student, academic_year=self.academic_year,
            event_name="MANUAL_REVIEW",
            new_workflow_state=WorkflowState.READY_FOR_FINALIZATION,
            new_vetting_status=VettingStatus.MANUALLY_VETTED,
            new_reason_codes=test_codes,
            actor=self.user
        )

        state = StudentState.objects.get(student=self.student, academic_year=self.academic_year)
        self.assertEqual(state.reason_codes, test_codes)

    def test_seeder_persists_reason_codes(self):
        """seed_student_state must generate and persist reason_codes."""
        state = seed_student_state(self.student, self.academic_year)
        self.assertIsNotNone(state.reason_codes)
        self.assertIn("message", state.reason_codes)


class TestUS14DuplicateTransitionLogs(TestCase):
    """US1.4: Re-seeding should only create log on created=True, not on updates."""

    def setUp(self):
        self.student = Student.objects.create(
            fiche=1008, full_name="Reseed Student",
            permanent_code="RSD1008001", is_active=True
        )
        self.academic_year = "2025-2026"

    def test_seeding_twice_creates_only_one_log(self):
        """First seed creates log; second seed (update) should NOT create log."""
        state1 = seed_student_state(self.student, self.academic_year)
        log_count_1 = StateTransitionLog.objects.filter(
            student=self.student, event_name='SYSTEM_SEED_INITIALIZATION'
        ).count()

        state2 = seed_student_state(self.student, self.academic_year)
        log_count_2 = StateTransitionLog.objects.filter(
            student=self.student, event_name='SYSTEM_SEED_INITIALIZATION'
        ).count()

        self.assertEqual(log_count_1, log_count_2)


class TestUS21IsActiveGuard(TestCase):
    """US2.1: apply_event must check is_active before allowing transitions."""

    def setUp(self):
        self.student = Student.objects.create(
            fiche=1009, full_name="Inactive Student",
            permanent_code="INAC1009001", is_active=False
        )
        self.academic_year = "2025-2026"
        self.user = User.objects.create(email="test5@test.com")

        StudentState.objects.create(
            student=self.student, academic_year=self.academic_year,
            workflow_state=WorkflowState.REGULAR_REVIEW_PENDING,
            vetting_status=VettingStatus.REQUIRES_REVIEW
        )

    def test_apply_event_inactive_student_raises_error(self):
        """Cannot apply event to inactive student."""
        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                student=self.student, academic_year=self.academic_year,
                event_name="MANUAL_REVIEW",
                new_workflow_state=WorkflowState.READY_FOR_FINALIZATION,
                actor=self.user
            )

        self.assertIn("inactive", str(cm.exception).lower())


class TestUS21DeFinalizationGuardBroadened(TestCase):
    """US2.1: De-finalization guard must prevent overwriting final_april_state."""

    def setUp(self):
        self.student = Student.objects.create(
            fiche=1010, full_name="Finalized Student",
            permanent_code="FINL1010001", is_active=True
        )
        self.academic_year = "2025-2026"
        self.user = User.objects.create(email="test6@test.com")

        StudentState.objects.create(
            student=self.student, academic_year=self.academic_year,
            workflow_state=WorkflowState.READY_FOR_FINALIZATION,
            final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
            vetting_status=VettingStatus.MANUALLY_VETTED
        )

    def test_cannot_overwrite_final_april_state(self):
        """Cannot change final_april_state once set."""
        with self.assertRaises(IllegalTransitionError):
            apply_event(
                student=self.student, academic_year=self.academic_year,
                event_name="OVERRIDE_STATE",
                new_final_april_state=FinalAprilState.APRIL_FINAL_HOLDBACK,
                actor=self.user
            )


class TestUS13ToStateSemanticAmbiguity(TestCase):
    """US1.3: to_state should have informative fallback, not empty string."""

    def setUp(self):
        self.student = Student.objects.create(
            fiche=1011, full_name="Final State Only",
            permanent_code="FSO1011001", is_active=True
        )
        self.academic_year = "2025-2026"
        self.user = User.objects.create(email="test7@test.com")

        StudentState.objects.create(
            student=self.student, academic_year=self.academic_year,
            workflow_state=None,
            final_april_state=None,
            vetting_status=VettingStatus.REQUIRES_REVIEW
        )

    def test_to_state_fallback_informative_not_empty(self):
        """When only final_april_state changes, to_state should not be empty."""
        apply_event(
            student=self.student, academic_year=self.academic_year,
            event_name="SET_FINAL_STATE",
            new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
            actor=self.user
        )

        log = StateTransitionLog.objects.filter(
            student=self.student, event_name='SET_FINAL_STATE'
        ).first()

        self.assertNotEqual(log.to_state, "")
        self.assertIn("FINAL_STATE_ONLY", log.to_state)

