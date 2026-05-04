from django.test import TestCase
from django.contrib.auth import get_user_model
from ninja.testing import TestClient
from ninja_jwt.tokens import RefreshToken
from core.api import api
from students.models import Student, StudentState, AcademicResult
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from school.models import Course, CourseOffering

User = get_user_model()

class QueueEndpointsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(email="admin@queues.com", password="password123")
        token = RefreshToken.for_user(self.user)
        self.client = TestClient(api, headers={"Authorization": f"Bearer {str(token.access_token)}"})
        
        self.academic_year = "2025-2026"
        
        # Setup common course
        self.course = Course.objects.create(
            local_code="MAT4",
            description="Mathématique 4",
            is_core_or_sanctioned=True
        )
        self.offering = CourseOffering.objects.create(
            course=self.course,
            academic_year=self.academic_year
        )

    def create_student_with_state(self, fiche, name, w_state, v_status):
        student = Student.objects.create(
            fiche=fiche,
            permanent_code=f"PC{fiche}",
            full_name=name,
            level="4",
            current_group="401"
        )
        state = StudentState.objects.create(
            student=student,
            academic_year=self.academic_year,
            workflow_state=w_state,
            vetting_status=v_status,
            reason_codes={"message": "Test reason"}
        )
        return student, state

    def test_ifp_queue_filtering(self):
        # Positive: IFP Candidate + REQUIRES_REVIEW
        s1, _ = self.create_student_with_state(101, "IFP Student", WorkflowState.IFP_CANDIDATE_REVIEW, VettingStatus.REQUIRES_REVIEW)
        
        # Negative: IFP Candidate + MANUALLY_VETTED (Should NOT appear)
        s2, _ = self.create_student_with_state(102, "Vetted IFP", WorkflowState.IFP_CANDIDATE_REVIEW, VettingStatus.MANUALLY_VETTED)
        
        # Negative: Regular Review + REQUIRES_REVIEW (Should NOT appear)
        s3, _ = self.create_student_with_state(103, "Regular Student", WorkflowState.REGULAR_REVIEW_PENDING, VettingStatus.REQUIRES_REVIEW)
        
        response = self.client.get("/students/queues/ifp")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        fiches = [item["fiche"] for item in data]
        self.assertIn(s1.fiche, fiches)
        self.assertNotIn(s2.fiche, fiches)
        self.assertNotIn(s3.fiche, fiches)
        self.assertEqual(data[0]["reason_codes"]["message"], "Test reason")

    def test_teacher_review_queue_filtering(self):
        # Positive: 57-59 grade + REQUIRES_REVIEW
        s1, _ = self.create_student_with_state(201, "Teacher Rev Student", WorkflowState.REGULAR_REVIEW_PENDING, VettingStatus.REQUIRES_REVIEW)
        AcademicResult.objects.create(student=s1, offering=self.offering, academic_year=self.academic_year, final_grade=58)
        
        # Negative: 55 grade (Too low for teacher review)
        s2, _ = self.create_student_with_state(202, "Low Grade Student", WorkflowState.REGULAR_REVIEW_PENDING, VettingStatus.REQUIRES_REVIEW)
        AcademicResult.objects.create(student=s2, offering=self.offering, academic_year=self.academic_year, final_grade=55)
        
        # Negative: 58 grade but MANUALLY_VETTED
        s3, _ = self.create_student_with_state(203, "Vetted Teacher Student", WorkflowState.REGULAR_REVIEW_PENDING, VettingStatus.MANUALLY_VETTED)
        AcademicResult.objects.create(student=s3, offering=self.offering, academic_year=self.academic_year, final_grade=58)
        
        response = self.client.get("/students/queues/teacher-review")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        fiches = [item["fiche"] for item in data]
        self.assertIn(s1.fiche, fiches)
        self.assertNotIn(s2.fiche, fiches)
        self.assertNotIn(s3.fiche, fiches)

    def test_summer_routing_queue_filtering(self):
        # Positive: 50-59 grade + REQUIRES_REVIEW
        s1, _ = self.create_student_with_state(301, "Summer Student", WorkflowState.REGULAR_REVIEW_PENDING, VettingStatus.REQUIRES_REVIEW)
        AcademicResult.objects.create(student=s1, offering=self.offering, academic_year=self.academic_year, final_grade=52)
        
        # Negative: 45 grade (Too low for summer school)
        s2, _ = self.create_student_with_state(302, "Too Low for Summer", WorkflowState.REGULAR_REVIEW_PENDING, VettingStatus.REQUIRES_REVIEW)
        AcademicResult.objects.create(student=s2, offering=self.offering, academic_year=self.academic_year, final_grade=45)
        
        # Negative: 52 grade but MANUALLY_VETTED
        s3, _ = self.create_student_with_state(303, "Vetted Summer", WorkflowState.REGULAR_REVIEW_PENDING, VettingStatus.MANUALLY_VETTED)
        AcademicResult.objects.create(student=s3, offering=self.offering, academic_year=self.academic_year, final_grade=52)
        
        response = self.client.get("/students/queues/summer")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        fiches = [item["fiche"] for item in data]
        self.assertIn(s1.fiche, fiches)
        self.assertNotIn(s2.fiche, fiches)
        self.assertNotIn(s3.fiche, fiches)
