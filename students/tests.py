from django.test import TestCase
from school.models import Course, CourseOffering, Teacher
from students.models import Student, AcademicResult
from django.contrib.auth import get_user_model

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
