from typing import Any

from django.test import TestCase
from django.contrib.auth import get_user_model
from ninja.testing import TestClient
from ninja_jwt.tokens import RefreshToken

from core.api import api
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from students.models import (
    Student,
    StudentPromotionOverride,
    SummerSchoolEnrollment,
    AcademicResult,
    StateTransitionLog,
)
from students.services.state_engine import apply_event, close_april_snapshot, IllegalTransitionError
from students.services.state_seeder import seed_student_state
from school.models import Course, CourseOffering

User = get_user_model()


class GrandCycleDeVieGpiTest(TestCase):
    def setUp(self):
        self.academic_year = "2025-2026"
        self.course = Course.objects.create(
            local_code="MAT401",
            description="Math 4",
            is_core_or_sanctioned=True,
            level=4,
            credits=4,
        )
        self.offering = CourseOffering.objects.create(
            course=self.course,
            group_number="401",
            academic_year=self.academic_year,
        )
        self.user = User.objects.create(email="emile.coordinator@test.com")
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)  # type: ignore[attr-defined]
        self.client: Any = TestClient(api, headers={"Authorization": f"Bearer {self.token}"})

        self.emile = Student.objects.create(
            fiche=7001,
            full_name="Émile",
            permanent_code="EMI70010001",
            level="Sec 4",
            current_group="401",
            is_active=True,
        )
        AcademicResult.objects.create(
            student=self.emile,
            offering=self.offering,
            academic_year=self.academic_year,
            final_grade=55,
        )
        self.override = StudentPromotionOverride.objects.create(
            student=self.emile,
            course=self.course,
            academic_year=self.academic_year,
            override_type="FORCE_PASS",
            reason="Dérogation héritée FORCE_PASS",
            created_by=self.user,
        )

    def test_grand_cycle_de_vie_gpi(self):
        # Étape 1: seed with inherited FORCE_PASS
        state = seed_student_state(self.emile, self.academic_year)
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR)
        self.assertEqual(state.vetting_status, VettingStatus.MANUALLY_VETTED)
        self.assertEqual(state.workflow_state, WorkflowState.READY_FOR_FINALIZATION)

        # Étape 2: illegal IFP transition must be rejected by the prerequisite guard
        with self.assertRaises(IllegalTransitionError):
            apply_event(
                student=self.emile,
                academic_year=self.academic_year,
                event_name="ILLEGAL_IFP_ATTEMPT",
                new_final_april_state=FinalAprilState.APRIL_FINAL_IFP_N,
                actor=self.user,
            )

        state.refresh_from_db()
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR)
        self.assertEqual(StateTransitionLog.objects.filter(student=self.emile).count(), 1)

        # Étape 3: legacy API enrollment bridges transparently to apply_event
        response = self.client.post(
            "/students/summer-school/enroll",
            json={
                "student_fiche": self.emile.fiche,
                "course_code": self.course.local_code,
                "academic_year": self.academic_year,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["student_fiche"], self.emile.fiche)
        self.assertEqual(payload["course_code"], self.course.local_code)
        self.assertEqual(payload["course_desc"], self.course.description)
        self.assertEqual(payload["academic_year"], self.academic_year)

        # Étape 4: physical DB synchronization
        state.refresh_from_db()
        self.assertEqual(state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER)
        self.assertEqual(state.workflow_state, WorkflowState.READY_FOR_FINALIZATION)
        enrollment = SummerSchoolEnrollment.objects.get(student=self.emile, academic_year=self.academic_year)
        self.assertEqual(enrollment.course, self.course)
        self.assertEqual(enrollment.enrolled_by, self.user)

        # Étape 5: precise audit trail
        log = StateTransitionLog.objects.get(student=self.emile, event_name="ASSIGN_SUMMER")
        self.assertEqual(log.to_workflow_state, WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(log.to_final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER)
        self.assertEqual(log.reason_payload["reason_codes"]["message"], "Manual override via Legacy API")
        self.assertEqual(log.reason_payload["message"], "Manual override via Legacy API")

        # Étape 6: final lock
        self.assertTrue(close_april_snapshot(self.academic_year))

