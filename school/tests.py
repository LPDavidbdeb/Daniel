from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
import unittest.mock as mock
from .models import Course, Teacher, CourseOffering

User = get_user_model()

class CoursePedagogicalMetadataTest(TestCase):
    def test_course_creation_with_metadata(self):
        """Vérifie la création d'un cours avec toutes ses métadonnées."""
        course = Course.objects.create(
            local_code="MAT406",
            description="Mathématiques SN",
            level=4,
            credits=4,
            is_core_or_sanctioned=True,
            periods=6,
            meq_code="123456"
        )
        self.assertEqual(course.local_code, "MAT406")
        self.assertEqual(course.level, 4)
        self.assertTrue(course.is_core_or_sanctioned)

    def test_course_default_values(self):
        """Vérifie qu'un cours créé avec l'ancien format hérite des bonnes valeurs par défaut."""
        course = Course.objects.create(
            local_code="ART101",
            description="Arts Plastiques"
        )
        self.assertIsNone(course.level)
        self.assertEqual(course.credits, 0)
        self.assertFalse(course.is_core_or_sanctioned)

    def test_course_filtering(self):
        """Valide le filtrage des cours par niveau."""
        Course.objects.create(local_code="FRA304", description="Français", level=3, is_core_or_sanctioned=True)
        Course.objects.create(local_code="MAT306", description="Maths", level=3, is_core_or_sanctioned=True)
        
        core_sec3 = Course.objects.filter(level=3, is_core_or_sanctioned=True)
        self.assertEqual(core_sec3.count(), 2)

    def test_duplicate_meq_code_different_local_code(self):
        """Vérifie qu'on peut avoir le même code MEQ pour des codes locaux différents."""
        Course.objects.create(local_code="FRA128", description="Français Régulier", meq_code="132108")
        Course.objects.create(local_code="FRA1Z8", description="Français Zénith", meq_code="132108")
        self.assertEqual(Course.objects.filter(meq_code="132108").count(), 2)

class SeedCoursesCommandTest(TestCase):
    @mock.patch("school.management.commands.seed_courses.os.path.exists")
    @mock.patch("school.management.commands.seed_courses.open", create=True)
    @mock.patch("school.management.commands.seed_courses.json.load")
    def test_seed_courses_success(self, mock_json_load, mock_open, mock_exists):
        """Vérifie que la commande crée bien les cours depuis le JSON."""
        mock_exists.return_value = True
        mock_json_load.return_value = [
            {
                "local_code": "SEED01",
                "meq_code": "111222",
                "description": "Cours Seed 1",
                "periods": 4,
                "level": 1,
                "is_core_or_sanctioned": True
            },
            {
                "local_code": "SEED02",
                "description": "Cours Seed 2",
                "periods": 2
            }
        ]

        call_command('seed_courses')
        self.assertEqual(Course.objects.filter(local_code__startswith="SEED").count(), 2)
        c1 = Course.objects.get(local_code="SEED01")
        self.assertEqual(c1.periods, 4)

    @mock.patch("school.management.commands.seed_courses.os.path.exists")
    @mock.patch("school.management.commands.seed_courses.open", create=True)
    @mock.patch("school.management.commands.seed_courses.json.load")
    def test_seed_courses_idempotency(self, mock_json_load, mock_open, mock_exists):
        """Vérifie que la commande ne duplique pas les cours."""
        mock_exists.return_value = True
        mock_json_load.return_value = [{"local_code": "IDEM01", "description": "Idempotent"}]

        call_command('seed_courses')
        call_command('seed_courses')
        self.assertEqual(Course.objects.filter(local_code="IDEM01").count(), 1)

    @mock.patch("school.management.commands.seed_courses.os.path.exists")
    def test_seed_courses_file_not_found(self, mock_exists):
        """Vérifie l'erreur si fichier manquant."""
        mock_exists.return_value = False
        with self.assertRaises(CommandError):
            call_command('seed_courses')

class CourseOfferingTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(local_code="FRA404", description="Français")
        user = User.objects.create(email="prof@test.com")
        self.teacher = Teacher.objects.create(user=user, full_name="Prof Test")

    def test_unique_offering_same_year(self):
        CourseOffering.objects.create(course=self.course, group_number="01", academic_year="2024-2025", teacher=self.teacher)
        with self.assertRaises(IntegrityError):
            CourseOffering.objects.create(course=self.course, group_number="01", academic_year="2024-2025", teacher=self.teacher)

    def test_duplicate_offering_different_years(self):
        CourseOffering.objects.create(course=self.course, group_number="01", academic_year="2024-2025", teacher=self.teacher)
        offering2 = CourseOffering.objects.create(course=self.course, group_number="01", academic_year="2025-2026", teacher=self.teacher)
        self.assertEqual(offering2.academic_year, "2025-2026")
