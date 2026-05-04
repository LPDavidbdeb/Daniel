from django.test import SimpleTestCase

class EnumsConstantsTest(SimpleTestCase):
    def test_imports(self):
        from students.enums import CourseState, WorkflowState, FinalAprilState, VettingStatus
        from students.constants import PASS_THRESHOLD, FAIL_HARD_BLOCK_THRESHOLD, TEACHER_REVIEW_MIN, MAX_SUMMER_CLASSES

    def test_course_state_enum(self):
        from students.enums import CourseState
        self.assertEqual(CourseState.PASS, "PASS")
        self.assertEqual(CourseState.FAIL_NON_SUMMER, "FAIL_NON_SUMMER")
        self.assertEqual(CourseState.SUMMER_ELIGIBLE, "SUMMER_ELIGIBLE")
        self.assertEqual(CourseState.SUMMER_ELIGIBLE_TEACHER_REVIEW, "SUMMER_ELIGIBLE_TEACHER_REVIEW")

    def test_workflow_state_enum(self):
        from students.enums import WorkflowState
        self.assertEqual(WorkflowState.IFP_CANDIDATE_REVIEW, "IFP_CANDIDATE_REVIEW")
        self.assertEqual(WorkflowState.REGULAR_REVIEW_PENDING, "REGULAR_REVIEW_PENDING")
        self.assertEqual(WorkflowState.READY_FOR_FINALIZATION, "READY_FOR_FINALIZATION")

    def test_final_april_state_enum(self):
        from students.enums import FinalAprilState
        self.assertEqual(FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR, "APRIL_FINAL_PROMOTE_REGULAR")
        self.assertEqual(FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER, "APRIL_FINAL_PROMOTE_WITH_SUMMER")
        self.assertEqual(FinalAprilState.APRIL_FINAL_HOLDBACK, "APRIL_FINAL_HOLDBACK")
        self.assertEqual(FinalAprilState.APRIL_FINAL_IFP_N, "APRIL_FINAL_IFP_N")
        self.assertEqual(FinalAprilState.APRIL_FINAL_IFP_N_MINUS_1, "APRIL_FINAL_IFP_N_MINUS_1")

    def test_vetting_status_enum(self):
        from students.enums import VettingStatus
        self.assertEqual(VettingStatus.AUTO_VETTED, "AUTO_VETTED")
        self.assertEqual(VettingStatus.REQUIRES_REVIEW, "REQUIRES_REVIEW")
        self.assertEqual(VettingStatus.MANUALLY_VETTED, "MANUALLY_VETTED")

    def test_policy_constants(self):
        from students.constants import PASS_THRESHOLD, FAIL_HARD_BLOCK_THRESHOLD, TEACHER_REVIEW_MIN, MAX_SUMMER_CLASSES
        self.assertEqual(PASS_THRESHOLD, 60)
        self.assertEqual(FAIL_HARD_BLOCK_THRESHOLD, 50)
        self.assertEqual(TEACHER_REVIEW_MIN, 57)
        self.assertEqual(MAX_SUMMER_CLASSES, 1)
