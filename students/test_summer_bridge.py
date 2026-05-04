from django.test import TestCase
from django.contrib.auth import get_user_model
from students.models import Student, StudentState, SummerSchoolEnrollment, AcademicResult, StateTransitionLog
from school.models import Course, CourseOffering
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from students.services.state_engine import apply_event

User = get_user_model()

class SummerBridgeTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            fiche=11001, full_name="Summer Test Student", 
            permanent_code="SUMM11001001", is_active=True
        )
        self.academic_year = "2025-2026"
        self.course = Course.objects.create(
            local_code="MAT401", description="Math 4", is_core_or_sanctioned=True
        )
        self.offering = CourseOffering.objects.create(
            course=self.course, group_number="401", academic_year=self.academic_year
        )
        self.user = User.objects.create(email="coordinator@test.com")
        
        # Initial state via seeding
        StudentState.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            workflow_state=WorkflowState.REGULAR_REVIEW_PENDING,
            vetting_status=VettingStatus.REQUIRES_REVIEW
        )
        
        # Student has a failing grade in Math
        AcademicResult.objects.create(
            student=self.student, offering=self.offering, 
            academic_year=self.academic_year, final_grade=52
        )

    def test_apply_event_creates_summer_enrollment(self):
        """Transitioning to PROMOTE_WITH_SUMMER should create a SummerSchoolEnrollment."""
        # Note: We pass the course_id in the payload
        apply_event(
            student=self.student,
            academic_year=self.academic_year,
            event_name="ASSIGN_SUMMER",
            new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER,
            new_vetting_status=VettingStatus.MANUALLY_VETTED,
            actor=self.user,
            payload={"course_id": self.course.id}
        )

        # Verify SummerSchoolEnrollment
        enrollment = SummerSchoolEnrollment.objects.filter(
            student=self.student, academic_year=self.academic_year
        ).first()
        self.assertIsNotNone(enrollment)
        self.assertEqual(enrollment.course, self.course)
        self.assertEqual(enrollment.enrolled_by, self.user)

    def test_apply_event_removes_summer_enrollment(self):
        """Transitioning AWAY from summer should remove the SummerSchoolEnrollment."""
        # Update grade to be eligible for teacher review override
        AcademicResult.objects.filter(student=self.student).update(final_grade=58)
        
        # 1. Setup existing enrollment
        SummerSchoolEnrollment.objects.create(
            student=self.student, course=self.course, 
            academic_year=self.academic_year, enrolled_by=self.user
        )
        
        # 2. Change state to PROMOTE_REGULAR (e.g. after teacher review)
        apply_event(
            student=self.student,
            academic_year=self.academic_year,
            event_name="TEACHER_REVIEW_PASS",
            new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
            new_vetting_status=VettingStatus.MANUALLY_VETTED,
            actor=self.user
        )

        # Verify SummerSchoolEnrollment is gone
        self.assertFalse(SummerSchoolEnrollment.objects.filter(
            student=self.student, academic_year=self.academic_year
        ).exists())

    def test_apply_event_upserts_summer_enrollment(self):
        """Transitioning to summer again with a different course should update it."""
        course2 = Course.objects.create(local_code="FRA401", description="French 4")
        
        # 1. Initial enrollment
        SummerSchoolEnrollment.objects.create(
            student=self.student, course=self.course, 
            academic_year=self.academic_year, enrolled_by=self.user
        )
        
        # 2. Update to a different course
        apply_event(
            student=self.student,
            academic_year=self.academic_year,
            event_name="SWITCH_SUMMER_COURSE",
            new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER,
            payload={"course_id": course2.id},
            actor=self.user
        )
        
        enrollment = SummerSchoolEnrollment.objects.get(
            student=self.student, academic_year=self.academic_year
        )
        self.assertEqual(enrollment.course, course2)

    def test_apply_event_audit_log_payload(self):
        """Audit log should confirm the legacy synchronization."""
        apply_event(
            student=self.student,
            academic_year=self.academic_year,
            event_name="ASSIGN_SUMMER",
            new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER,
            payload={"course_id": self.course.id},
            actor=self.user
        )
        
        log = StateTransitionLog.objects.filter(student=self.student, event_name="ASSIGN_SUMMER").first()
        self.assertEqual(log.reason_payload["legacy_summer_sync"], "CREATED_OR_UPDATED")
        self.assertEqual(log.reason_payload["course_code"], self.course.local_code)
