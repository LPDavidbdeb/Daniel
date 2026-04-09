from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from .models import Course, Teacher, CourseOffering

User = get_user_model()

class CourseOfferingTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(code="FRA404", description="Français")
        user = User.objects.create(email="prof@test.com")
        self.teacher = Teacher.objects.create(user=user, full_name="Prof Test")

    def test_unique_offering_same_year(self):
        # Création de la première offre
        CourseOffering.objects.create(
            course=self.course, 
            group_number="01", 
            academic_year="2024-2025",
            teacher=self.teacher
        )
        # Tentative de création d'une offre identique la même année -> Doit échouer
        with self.assertRaises(IntegrityError):
            CourseOffering.objects.create(
                course=self.course, 
                group_number="01", 
                academic_year="2024-2025",
                teacher=self.teacher
            )

    def test_duplicate_offering_different_years(self):
        # Création la même offre mais sur deux années différentes -> Doit réussir
        CourseOffering.objects.create(
            course=self.course, 
            group_number="01", 
            academic_year="2024-2025",
            teacher=self.teacher
        )
        offering2 = CourseOffering.objects.create(
            course=self.course, 
            group_number="01", 
            academic_year="2025-2026",
            teacher=self.teacher
        )
        self.assertEqual(offering2.academic_year, "2025-2026")
