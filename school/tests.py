from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
import json
from .models import Course, Teacher, CourseOffering, Cohort, MeqReference
from students.models import Student

User = get_user_model()

class CoursePedagogicalMetadataTest(TestCase):
    def test_course_creation_with_metadata(self):
        course = Course.objects.create(local_code="MAT406", description="Maths SN", level=4, credits=4, is_core_or_sanctioned=True)
        self.assertEqual(course.local_code, "MAT406")

    def test_duplicate_meq_code_different_local_code(self):
        Course.objects.create(local_code="FRA128", description="Français Reg", meq_code="132108")
        Course.objects.create(local_code="FRA1Z8", description="Français Zen", meq_code="132108")
        self.assertEqual(Course.objects.filter(meq_code="132108").count(), 2)

class CohortTest(TestCase):
    def test_cohort_creation_and_students(self):
        """Vérifie la création d'une cohorte et l'ajout d'élèves."""
        student = Student.objects.create(fiche=999, full_name="Student Test", permanent_code="TEST99999999")
        cohort = Cohort.objects.create(name="Zénith Sec 1", cohort_type="ZENITH", academic_year="2025-2026")
        cohort.students.add(student)
        
        self.assertEqual(cohort.students.count(), 1)
        self.assertEqual(student.cohorts.first().name, "Zénith Sec 1")

class CourseOfferingTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(local_code="FRA404", description="Français")
        user = User.objects.create(email="prof@test.com")
        self.teacher = Teacher.objects.create(user=user, full_name="Prof Test")

    def test_unique_offering_same_year(self):
        CourseOffering.objects.create(course=self.course, group_number="01", academic_year="2024-2025", teacher=self.teacher)
        with self.assertRaises(IntegrityError):
            CourseOffering.objects.create(course=self.course, group_number="01", academic_year="2024-2025", teacher=self.teacher)


class CourseMeqValidationApiTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(email="admin@test.com", password="Test1234!!")
        token_response = self.client.post(
            "/api/token/pair",
            data=json.dumps({"email": self.superuser.email, "password": "Test1234!!"}),
            content_type="application/json",
        )
        self.assertEqual(token_response.status_code, 200)
        self.auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {token_response.json()['access']}"
        }

    def test_api_rejects_invalid_meq_code_on_course_creation(self):
        payload = {
            "local_code": "LOC999",
            "meq_code": "999999",
            "description": "Cours invalide",
            "level": 4,
            "credits": 4,
            "periods": 8,
            "is_core_or_sanctioned": False,
            "is_active": True,
        }

        response = self.client.post(
            "/api/school/crud/courses",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json().get("detail"),
            "Le code MEQ fourni n'existe pas dans le référentiel officiel du Ministère.",
        )
        self.assertFalse(Course.objects.filter(local_code="LOC999").exists())

    def test_api_accepts_valid_meq_code_on_course_creation(self):
        MeqReference.objects.create(
            meq_code="132108",
            description="Français langue d'enseignement",
            credits=8,
        )
        payload = {
            "local_code": "FRA128",
            "meq_code": "132108",
            "description": "Français régulier",
            "level": 1,
            "credits": 8,
            "periods": 8,
            "is_core_or_sanctioned": True,
            "is_active": True,
        }

        response = self.client.post(
            "/api/school/crud/courses",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("meq_code"), "132108")
        self.assertTrue(Course.objects.filter(local_code="FRA128", meq_code="132108").exists())

