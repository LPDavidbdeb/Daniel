from django.test import TestCase
from django.db.utils import IntegrityError
from school.models import Course, CourseOffering, Teacher
from students.models import Student, AcademicResult, StudentPromotionOverride
from django.contrib.auth import get_user_model

User = get_user_model()

class AcademicResultTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(fiche=123, full_name="John Doe", permanent_code="ABCD12345678")
        self.course = Course.objects.create(local_code="MAT101", description="Maths")
        user = User.objects.create(email="prof@test.com")
        self.teacher = Teacher.objects.create(user=user, full_name="Prof Test")
        self.offering = CourseOffering.objects.create(course=self.course, group_number="01", academic_year="2024-2025", teacher=self.teacher)

    def test_create_result_with_year(self):
        res = AcademicResult.objects.create(student=self.student, offering=self.offering, academic_year="2024-2025", final_grade=85)
        self.assertEqual(res.academic_year, "2024-2025")

class StudentOverrideTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(fiche=888, full_name="Override Test", permanent_code="OVER88888888")
        self.course = Course.objects.create(local_code="FRA128", description="Français")

    def test_unique_override(self):
        """Vérifie qu'on ne peut pas doubler une dérogation pour le même élève/cours/année."""
        StudentPromotionOverride.objects.create(
            student=self.student,
            course=self.course,
            academic_year="2025-2026",
            override_type="FORCE_PASS"
        )
        with self.assertRaises(IntegrityError):
            StudentPromotionOverride.objects.create(
                student=self.student,
                course=self.course,
                academic_year="2025-2026",
                override_type="FORCE_RETAKE"
            )
