from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from time import sleep
from students.models import Student, StateTransitionLog
from students.enums import WorkflowState

User = get_user_model()

class StateTransitionLogTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            fiche=2001,
            full_name="Bob Brown",
            permanent_code="BROB20010001",
            level="Sec 4",
            current_group="402"
        )
        self.user = User.objects.create(email="admin@test.com")

    def test_create_log_system_event(self):
        """Test creating a log entry for a system event (no actor)."""
        log = StateTransitionLog.objects.create(
            student=self.student,
            from_state=None,
            to_state=WorkflowState.REGULAR_REVIEW_PENDING,
            event_name="SYSTEM_AUTO_CLASSIFY",
            reason_payload={"detail": "Initial classification"}
        )
        self.assertEqual(log.student, self.student)
        self.assertIsNone(log.from_state)
        self.assertEqual(log.to_state, WorkflowState.REGULAR_REVIEW_PENDING)
        self.assertEqual(log.event_name, "SYSTEM_AUTO_CLASSIFY")
        self.assertIsNone(log.actor)
        self.assertEqual(log.reason_payload, {"detail": "Initial classification"})
        self.assertIsNotNone(log.timestamp)

    def test_create_log_user_event(self):
        """Test creating a log entry for a user-triggered event."""
        log = StateTransitionLog.objects.create(
            student=self.student,
            from_state=WorkflowState.REGULAR_REVIEW_PENDING,
            to_state=WorkflowState.READY_FOR_FINALIZATION,
            event_name="TEACHER_REVIEW_PASS",
            actor=self.user,
            reason_payload={"note": "Reviewed and approved"}
        )
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.from_state, WorkflowState.REGULAR_REVIEW_PENDING)
        self.assertEqual(log.to_state, WorkflowState.READY_FOR_FINALIZATION)

    def test_ordering_and_indexing(self):
        """Test that logs are ordered by timestamp descending."""
        log1 = StateTransitionLog.objects.create(
            student=self.student,
            from_state=None,
            to_state="STATE_1",
            event_name="EVENT_1"
        )
        sleep(0.01) # Ensure timestamp difference
        log2 = StateTransitionLog.objects.create(
            student=self.student,
            from_state="STATE_1",
            to_state="STATE_2",
            event_name="EVENT_2"
        )
        
        logs = StateTransitionLog.objects.filter(student=self.student)
        self.assertEqual(logs[0], log2)
        self.assertEqual(logs[1], log1)
