from django.test import TestCase
from students.enums import CourseEvalState, WorkflowState, FinalAprilState, VettingStatus
from students.services.auto_derivation import aggregate_micro_results


class LevelDifferentiationTest(TestCase):
    """Ensure macro decisions vary by student level (Sec 1 vs Sec 4)."""

    def test_same_failed_bulletin_differs_by_level(self):
        """
        Same failed micro bulletin, different level policies:
        - Sec 1: HOLDBACK (lenient)
        - Sec 4: IFP_CANDIDATE_REVIEW (strict)
        """
        micro_states = {"MAT200": CourseEvalState.FAILED}
        reason_codes_by_state = {
            CourseEvalState.PASS: [],
            CourseEvalState.TEACHER_REVIEW_PENDING: [],
            CourseEvalState.SUMMER_ELIGIBLE: [],
            CourseEvalState.FAILED: ["MAT200 (52%)"],
        }

        sec1_workflow, sec1_final, sec1_vetting, sec1_payload = aggregate_micro_results(
            micro_states,
            reason_codes_by_state,
            student_level="Sec 1",
        )
        sec4_workflow, sec4_final, sec4_vetting, sec4_payload = aggregate_micro_results(
            micro_states,
            reason_codes_by_state,
            student_level="Sec 4",
        )

        self.assertNotEqual(sec1_workflow, sec4_workflow)

        self.assertEqual(sec1_workflow, WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(sec1_final, FinalAprilState.APRIL_FINAL_HOLDBACK)
        self.assertEqual(sec1_vetting, VettingStatus.REQUIRES_REVIEW)
        self.assertEqual(sec1_payload["rule"], "LEVEL_SEC_1_HOLDBACK")

        self.assertEqual(sec4_workflow, WorkflowState.IFP_CANDIDATE_REVIEW)
        self.assertIsNone(sec4_final)
        self.assertEqual(sec4_vetting, VettingStatus.REQUIRES_REVIEW)
        self.assertEqual(sec4_payload["rule"], "LEVEL_SEC_4_IFP")
