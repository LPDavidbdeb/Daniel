from django.test import TestCase
from school.models import Course, CourseOffering, Teacher
from students.models import Student, AcademicResult
from django.contrib.auth import get_user_model
from types import SimpleNamespace
from students.api import create_student_crud, update_student_crud, delete_student_crud, list_students_crud
from students.schemas import StudentCrudIn

User = get_user_model()

class AcademicResultTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(fiche=123, full_name="John Doe", permanent_code="ABCD12345678")
        self.course = Course.objects.create(local_code="MAT101", description="Maths")
        user = User.objects.create(email="prof@test.com")
        self.teacher = Teacher.objects.create(user=user, full_name="Prof Test")
        self.offering = CourseOffering.objects.create(
            course=self.course, 
            group_number="01", 
            academic_year="2024-2025",
            teacher=self.teacher
        )

    def test_create_result_with_year(self):
        res = AcademicResult.objects.create(
            student=self.student,
            offering=self.offering,
            academic_year="2024-2025",
            final_grade=85
        )
        self.assertEqual(res.academic_year, "2024-2025")

    def test_filter_by_year(self):
        AcademicResult.objects.create(
            student=self.student,
            offering=self.offering,
            academic_year="2024-2025",
            final_grade=85
        )
        count = AcademicResult.objects.filter(academic_year="2024-2025").count()
        self.assertEqual(count, 1)
        
        count_other = AcademicResult.objects.filter(academic_year="2023-2024").count()
        self.assertEqual(count_other, 0)


class StudentCrudTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create(email='admin@test.com')
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()
        self.request = SimpleNamespace(user=self.superuser)

    def test_create_list_update_delete_student(self):
        created = create_student_crud(self.request, StudentCrudIn(
            fiche=1001,
            permanent_code='PCODE1001',
            full_name='Nouvel Eleve',
            level='3',
            current_group='301',
            is_active=True,
        ))
        self.assertEqual(created.fiche, 1001)

        students = list_students_crud(self.request)
        self.assertEqual(len(students), 1)

        updated = update_student_crud(self.request, 1001, StudentCrudIn(
            fiche=1001,
            permanent_code='PCODE1001X',
            full_name='Eleve Mis A Jour',
            level='4',
            current_group='402',
            is_active=False,
        ))
        self.assertEqual(updated.full_name, 'Eleve Mis A Jour')
        self.assertFalse(updated.is_active)

        delete_student_crud(self.request, 1001)
        self.assertEqual(Student.objects.count(), 0)

