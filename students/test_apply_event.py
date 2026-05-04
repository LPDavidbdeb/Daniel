from django.test import TestCase
from django.contrib.auth import get_user_model
from students.models import Student, StudentState, StateTransitionLog
from students.enums import WorkflowState, FinalAprilState
from students.services.state_engine import apply_event, IllegalTransitionError

User = get_user_model()

class ApplyEventTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            fiche=6001,
            full_name="Gateway Test",
            permanent_code="GATA60010001",
            level="Sec 5",
            is_active=True
        )
        self.academic_year = "2025-2026"
        self.user = User.objects.create(email="coordinator@test.com")
        
        # Initial state
        self.state = StudentState.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            workflow_state=WorkflowState.REGULAR_REVIEW_PENDING,
            vetting_status="REQUIRES_REVIEW"
        )

    def test_apply_event_success(self):
        """A legal transition updates the state and creates a log."""
        payload = {"reason": "Test success"}
        apply_event(
            student=self.student,
            academic_year=self.academic_year,
            event_name="TEST_APPROVE",
            new_workflow_state=WorkflowState.READY_FOR_FINALIZATION,
            actor=self.user,
            payload=payload
        )

        # Verify StudentState
        self.state.refresh_from_db()
        self.assertEqual(self.state.workflow_state, WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(self.state.version, 2)

        # Verify Log
        log = StateTransitionLog.objects.filter(student=self.student).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.from_state, WorkflowState.REGULAR_REVIEW_PENDING)
        self.assertEqual(log.to_state, WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(log.event_name, "TEST_APPROVE")
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.reason_payload["reason"], payload["reason"])
        self.assertEqual(log.reason_payload["version"], 2)

    def test_apply_event_illegal_transition(self):
        """Transitions from a finalized state should be rejected."""
        # Manually set to a finalized state
        self.state.workflow_state = WorkflowState.READY_FOR_FINALIZATION
        self.state.final_april_state = FinalAprilState.APRIL_FINAL_HOLDBACK
        self.state.save()

        # Try to move back to pending (illegal for this test's logic)
        with self.assertRaises(IllegalTransitionError):
            apply_event(
                student=self.student,
                academic_year=self.academic_year,
                event_name="TEST_REOPEN",
                new_workflow_state=WorkflowState.REGULAR_REVIEW_PENDING,
                actor=self.user
            )

        # Verify no changes (atomic)
        self.state.refresh_from_db()
        self.assertEqual(self.state.workflow_state, WorkflowState.READY_FOR_FINALIZATION)
        self.assertEqual(StateTransitionLog.objects.filter(event_name="TEST_REOPEN").count(), 0)

    def test_apply_event_invalid_enum(self):
        """New state must be a valid enum value."""
        with self.assertRaises(IllegalTransitionError):
            apply_event(
                student=self.student,
                academic_year=self.academic_year,
                event_name="TEST_INVALID",
                new_workflow_state="NOT_A_STATE",
                actor=self.user
            )
