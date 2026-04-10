from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
import unittest.mock as mock
from .models import Course, Teacher, CourseOffering, Cohort
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
