from typing import Any

from django.test import TestCase
from django.contrib.auth import get_user_model
from ninja.testing import TestClient
from ninja_jwt.tokens import RefreshToken

from core.api import api
from students.enums import VettingStatus
from students.models import Student, StudentState

User = get_user_model()


class VettingStatusApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="vetting-api@test.com", is_staff=True, is_superuser=True)
        refresh = RefreshToken.for_user(self.user)
        token = str(refresh.access_token)  # type: ignore[attr-defined]
        self.client: Any = TestClient(api, headers={"Authorization": f"Bearer {token}"})
        self.academic_year = "2025-2026"

        self.student = Student.objects.create(
            fiche=8801,
            permanent_code="API88010001",
            full_name="Etudiant Vetting",
            level="Sec 4",
            current_group="401",
            is_active=True,
        )
        StudentState.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            vetting_status=VettingStatus.REQUIRES_REVIEW,
        )

    def test_list_endpoint_includes_vetting_status(self):
        response = self.client.get("/students/crud/students")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(len(payload) > 0)
        student_json = next(s for s in payload if s["fiche"] == self.student.fiche)
        self.assertIn("vetting_status", student_json)
        self.assertEqual(student_json["vetting_status"], VettingStatus.REQUIRES_REVIEW)

    def test_detail_endpoint_includes_vetting_status(self):
        response = self.client.get(f"/students/{self.student.fiche}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("vetting_status", payload)
        self.assertEqual(payload["vetting_status"], VettingStatus.REQUIRES_REVIEW)

    def test_group_list_endpoint_includes_exact_requires_review(self):
        response = self.client.get("/students/groups/401/students")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        student_json = next(s for s in payload if s["fiche"] == self.student.fiche)
        self.assertEqual(student_json["vetting_status"], "REQUIRES_REVIEW")


