from django.test import TestCase
from django.contrib.auth import get_user_model
from ninja.testing import TestClient
from ninja_jwt.tokens import RefreshToken

from core.api import api
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from students.models import (
    Student,
    StudentState,
    SummerSchoolEnrollment,
    StudentPromotionOverride,
    StateTransitionLog,
)
from school.models import Course, CourseOffering

User = get_user_model()


class ApiBridgeCompatibilityTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="bridge@test.com")
        access_token = str(RefreshToken.for_user(self.user).access_token)
        self.client = TestClient(api, headers={"Authorization": f"Bearer {access_token}"})
        self.academic_year = "2025-2026"
        self.course = Course.objects.create(
            local_code="MAT401",
            description="Math 4",
            is_core_or_sanctioned=True,
        )
        self.offering = CourseOffering.objects.create(
            course=self.course,
            group_number="401",
            academic_year=self.academic_year,
        )

    def test_summer_school_enroll_bridges_legacy_state_and_audit(self):
        student = Student.objects.create(
            fiche=9101,
            full_name="Bridge Summer Student",
            permanent_code="BRG91010001",
            level="Sec 5",
            current_group="501",
            is_active=True,
        )

        response = self.client.post(
            "/students/summer-school/enroll",
            json={
                "student_fiche": student.fiche,
                "course_code": self.course.local_code,
                "academic_year": self.academic_year,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["student_fiche"], student.fiche)
        self.assertEqual(response.json()["course_code"], self.course.local_code)
        self.assertEqual(response.json()["course_desc"], self.course.description)

        enrollment = SummerSchoolEnrollment.objects.get(student=student, academic_year=self.academic_year)
        self.assertEqual(enrollment.course, self.course)
        self.assertEqual(enrollment.enrolled_by, self.user)

        state = StudentState.objects.get(student=student, academic_year=self.academic_year)
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER)
        self.assertEqual(state.vetting_status, VettingStatus.MANUALLY_VETTED)

        log = StateTransitionLog.objects.filter(student=student, event_name="ASSIGN_SUMMER").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.reason_payload["summer_sync"], "CREATED_OR_UPDATED")
        self.assertEqual(log.reason_payload["course_code"], self.course.local_code)

    def test_summer_school_cancel_bridges_legacy_state_and_audit(self):
        student = Student.objects.create(
            fiche=9102,
            full_name="Bridge Summer Cancel Student",
            permanent_code="BRG91020001",
            level="Sec 5",
            current_group="501",
            is_active=True,
        )
        enrollment = SummerSchoolEnrollment.objects.create(
            student=student,
            course=self.course,
            academic_year=self.academic_year,
            enrolled_by=self.user,
        )
        StudentState.objects.create(
            student=student,
            academic_year=self.academic_year,
            workflow_state=WorkflowState.READY_FOR_FINALIZATION,
            final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER,
            vetting_status=VettingStatus.MANUALLY_VETTED,
        )

        response = self.client.delete(f"/students/summer-school/{enrollment.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.assertFalse(SummerSchoolEnrollment.objects.filter(student=student, academic_year=self.academic_year).exists())

        state = StudentState.objects.get(student=student, academic_year=self.academic_year)
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR)
        self.assertEqual(state.vetting_status, VettingStatus.MANUALLY_VETTED)

        log = StateTransitionLog.objects.filter(student=student, event_name="REMOVE_SUMMER").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.reason_payload["summer_sync"], "DELETED")

    def test_manual_vetting_bridge_updates_override_state_and_audit(self):
        student = Student.objects.create(
            fiche=9103,
            full_name="Bridge Triages Student",
            permanent_code="BRG91030001",
            level="Sec 5",
            current_group="501",
            is_active=True,
        )

        response = self.client.post(
            f"/students/{student.fiche}/evaluation",
            json={
                "academic_year": self.academic_year,
                "action": "MANUAL_VETTING",
                "course_code": self.course.local_code,
                "override_type": "FORCE_PASS",
                "reason": "Révision manuelle validée",
                "new_workflow_state": WorkflowState.READY_FOR_FINALIZATION,
                "new_final_april_state": FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["student_id"], student.fiche)
        self.assertEqual(response.json()["academic_year"], self.academic_year)
        self.assertFalse(response.json()["requires_review"])

        override = StudentPromotionOverride.objects.get(
            student=student,
            course=self.course,
            academic_year=self.academic_year,
        )
        self.assertEqual(override.override_type, "FORCE_PASS")
        self.assertEqual(override.reason, "Révision manuelle validée")

        state = StudentState.objects.get(student=student, academic_year=self.academic_year)
        self.assertEqual(state.workflow_state, WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR)
        self.assertEqual(state.vetting_status, VettingStatus.MANUALLY_VETTED)

        log = StateTransitionLog.objects.filter(student=student, event_name="MANUAL_VETTING").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.reason_payload["action"], "MANUAL_VETTING")
        self.assertEqual(log.reason_payload["override_type"], "FORCE_PASS")

