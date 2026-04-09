from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
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
        self.assertEqual(course.credits, 4)
        self.assertEqual(course.periods, 6)
        self.assertEqual(course.meq_code, "123456")
        self.assertTrue(course.is_core_or_sanctioned)

    def test_course_default_values(self):
        """Vérifie qu'un cours créé avec l'ancien format hérite des bonnes valeurs par défaut."""
        course = Course.objects.create(
            local_code="ART101",
            description="Arts Plastiques"
        )
        self.assertIsNone(course.level)
        self.assertEqual(course.credits, 0)
        self.assertEqual(course.periods, 0)
        self.assertIsNone(course.meq_code)
        self.assertFalse(course.is_core_or_sanctioned)

    def test_course_filtering(self):
        """Valide le filtrage des cours par niveau et statut de matière de base."""
        Course.objects.create(local_code="FRA304", description="Français", level=3, is_core_or_sanctioned=True)
        Course.objects.create(local_code="MAT306", description="Maths", level=3, is_core_or_sanctioned=True)
        Course.objects.create(local_code="ANG304", description="Anglais", level=3, is_core_or_sanctioned=False)
        Course.objects.create(local_code="FRA404", description="Français", level=4, is_core_or_sanctioned=True)

        # Filtrage level=3 et core=True
        core_sec3 = Course.objects.filter(level=3, is_core_or_sanctioned=True)
        self.assertEqual(core_sec3.count(), 2)
        codes = [c.local_code for c in core_sec3]
        self.assertIn("FRA304", codes)
        self.assertIn("MAT306", codes)

    def test_duplicate_meq_code_different_local_code(self):
        """Vérifie qu'on peut avoir le même code MEQ pour des codes locaux différents."""
        Course.objects.create(local_code="FRA128", description="Français Régulier", meq_code="132108")
        # Doit passer sans erreur
        Course.objects.create(local_code="FRA1Z8", description="Français Zénith", meq_code="132108")
        
        self.assertEqual(Course.objects.filter(meq_code="132108").count(), 2)

class CourseOfferingTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(local_code="FRA404", description="Français")
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
