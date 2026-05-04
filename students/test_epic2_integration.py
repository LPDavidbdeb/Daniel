"""
Epic 2 End-to-End Integration Test Suite
=========================================
Verifies the complete Orchestration Service as a cohesive whole.

Components under test:
  US2.1 — apply_event gateway          (students/services/state_engine.py)
  US2.2 — Invariant Guards             (students/services/transition_guards.py)
  US2.3 — Auto-Derivation service      (students/services/auto_derivation.py)
  US2.4 — close_april_snapshot gate    (students/services/state_engine.py)

Primary scenario: "The Blocked Closure" — a teacher-review student blocks
snapshot closure until a teacher legitimately resolves the case.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from students.models import Student, StudentState, StateTransitionLog, AcademicResult
from school.models import Course, CourseOffering
from students.enums import WorkflowState, FinalAprilState, VettingStatus
from students.services.state_engine import (
    apply_event,
    close_april_snapshot,
    IllegalTransitionError,
    SnapshotClosureError,
)
from students.services.auto_derivation import derive_student_state

User = get_user_model()


class Epic2BlockedClosureTest(TestCase):
    """
    Six-step adversarial sequence that exercises every Epic 2 component in order.

    Student profile: active, Sec 1, single core course with a grade-58 result.
    Grade 58 sits in the teacher-review zone (57 ≤ grade < 60) — the student
    fails mathematically but a teacher can legitimately pass them.
    """

    def setUp(self):
        self.academic_year = "2025-2026"
        self.teacher = User.objects.create(email="teacher@school.test")

        self.course = Course.objects.create(
            local_code="MAT-S1-E2",
            description="Mathématique Secondaire 1 (Epic 2 Test)",
            is_core_or_sanctioned=True,
            level=1,
            credits=4,
        )
        self.offering = CourseOffering.objects.create(
            course=self.course,
            group_number="G1",
            academic_year=self.academic_year,
        )

        self.student = Student.objects.create(
            fiche=6001,
            full_name="Marie Dubois",
            permanent_code="DUB60010001",
            level="Sec 1",
            current_group="101",
            is_active=True,
        )

        # Uninitialised state: no workflow assigned yet, default REQUIRES_REVIEW
        self.state = StudentState.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            vetting_status=VettingStatus.REQUIRES_REVIEW,
        )

        # Core course result in the teacher-review zone
        self.result = AcademicResult.objects.create(
            student=self.student,
            offering=self.offering,
            academic_year=self.academic_year,
            final_grade=58,
        )

    # ------------------------------------------------------------------ #
    #  MAIN SCENARIO                                                       #
    # ------------------------------------------------------------------ #

    def test_blocked_closure_scenario(self):
        """
        Full six-step sequence verifying Epic 2 end-to-end.

        1. derive_student_state classifies grade-58 student as Teacher Review.
        2. apply_event persists the suggested pending state without obstruction.
        3. close_april_snapshot is blocked by the unvetted student.
        4. An illegal IFP assignment is rejected by the Invariant Guard.
        5. The teacher legitimately resolves the case via apply_event.
        6. close_april_snapshot succeeds with all students vetted.
        """

        # ============================================================ #
        # STEP 1 — Auto-Derivation (US2.3)
        # Grade 58: single failure (58 < 60), in teacher-review range (57 ≤ 58 < 60),
        # no hard blocker (58 ≥ 50).  Rule 2 fires → Teacher Review Queue.
        # ============================================================ #
        suggestion = derive_student_state(self.student, self.academic_year)

        self.assertEqual(
            suggestion["workflow_state"],
            WorkflowState.REGULAR_REVIEW_PENDING,
            "Grade 58 must be routed to REGULAR_REVIEW_PENDING (Teacher Review Queue).",
        )
        self.assertIsNone(
            suggestion["final_april_state"],
            "No final state should be auto-assigned for a teacher-review case.",
        )
        self.assertEqual(
            suggestion["vetting_status"],
            VettingStatus.REQUIRES_REVIEW,
            "Teacher-review students must be flagged REQUIRES_REVIEW by derivation.",
        )
        # New Micro/Macro architecture: message format updated
        self.assertIn("Teacher Review", suggestion["reason_codes"]["message"])
        self.assertEqual(suggestion["reason_codes"]["rule"], "TEACHER_REVIEW_PRIORITY")

        # ============================================================ #
        # STEP 2 — Orchestration via apply_event (US2.1)
        # Apply the derivation result.  No guard should fire for a plain
        # workflow-state update (no final_april_state is being set).
        # ============================================================ #
        updated_state = apply_event(
            student=self.student,
            academic_year=self.academic_year,
            event_name="AUTO_DERIVATION_APPLIED",
            new_workflow_state=suggestion["workflow_state"],
            new_vetting_status=suggestion["vetting_status"],
            actor=None,  # system-triggered, no human actor
            payload={"source": "derive_student_state", "final_grade": 58},
        )

        self.assertEqual(updated_state.workflow_state, WorkflowState.REGULAR_REVIEW_PENDING)
        self.assertEqual(updated_state.vetting_status, VettingStatus.REQUIRES_REVIEW)
        self.assertEqual(updated_state.version, 2, "Version must increment on every successful apply_event.")

        log = StateTransitionLog.objects.get(student=self.student)  # exactly one
        self.assertEqual(log.event_name, "AUTO_DERIVATION_APPLIED")
        self.assertIsNone(log.actor, "System-triggered events have no human actor.")

        # ============================================================ #
        # STEP 3 — Snapshot gate blocks pending student (US2.4)
        # One active student still carries REQUIRES_REVIEW — closure must fail.
        # ============================================================ #
        with self.assertRaises(SnapshotClosureError) as cm:
            close_april_snapshot(self.academic_year)

        blocked_fiches = [s["fiche"] for s in cm.exception.incomplete_students]
        self.assertIn(
            self.student.fiche,
            blocked_fiches,
            "SnapshotClosureError must identify the unvetted student by fiche.",
        )

        # ============================================================ #
        # STEP 4 — Invariant Guard blocks illegal transition (US2.2)
        # Attempting to assign APRIL_FINAL_IFP_N while the student is in
        # REGULAR_REVIEW_PENDING violates the IFP Prerequisite Guard:
        # only students who went through IFP_CANDIDATE_REVIEW may receive
        # an IFP final outcome.
        # ============================================================ #
        version_before_attempt = updated_state.version  # 2
        logs_before_attempt = StateTransitionLog.objects.filter(student=self.student).count()  # 1

        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                student=self.student,
                academic_year=self.academic_year,
                event_name="ILLEGAL_IFP_BYPASS",
                new_final_april_state=FinalAprilState.APRIL_FINAL_IFP_N,
                actor=self.teacher,
                payload={"reason": "Bypassing IFP review pathway"},
            )

        self.assertIn(
            "IFP_CANDIDATE_REVIEW",
            str(cm.exception),
            "Guard error message must name the violated prerequisite.",
        )

        # The atomic transaction was rolled back — ledger and audit trail must be pristine
        self.state.refresh_from_db()
        self.assertEqual(
            self.state.version,
            version_before_attempt,
            "Rolled-back transition must leave StudentState.version unchanged.",
        )
        self.assertIsNone(
            self.state.final_april_state,
            "Rolled-back transition must leave final_april_state as None.",
        )
        self.assertEqual(
            StateTransitionLog.objects.filter(student=self.student).count(),
            logs_before_attempt,
            "A rejected transition must not produce an audit log entry.",
        )

        # ============================================================ #
        # STEP 5 — Teacher legitimately resolves the case (US2.1 + US2.2)
        # Grade 58 ≥ TEACHER_REVIEW_MIN (57): the Teacher Review Boundary Guard
        # permits promoting the student to APRIL_FINAL_PROMOTE_REGULAR.
        # ============================================================ #
        resolved_state = apply_event(
            student=self.student,
            academic_year=self.academic_year,
            event_name="TEACHER_REVIEW_PASS",
            new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
            new_vetting_status=VettingStatus.MANUALLY_VETTED,
            actor=self.teacher,
            payload={"reason": "Academic record reviewed; student passes by teacher judgement."},
        )

        self.assertEqual(resolved_state.final_april_state, FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR)
        self.assertEqual(resolved_state.vetting_status, VettingStatus.MANUALLY_VETTED)
        self.assertEqual(resolved_state.version, 3)

        latest_log = StateTransitionLog.objects.filter(student=self.student).first()
        self.assertEqual(latest_log.event_name, "TEACHER_REVIEW_PASS")
        self.assertEqual(latest_log.actor, self.teacher)
        self.assertEqual(
            StateTransitionLog.objects.filter(student=self.student).count(),
            2,
            "Two successful transitions must produce exactly two audit entries.",
        )

        # ============================================================ #
        # STEP 6 — Final Closure: snapshot gate must now succeed (US2.4)
        # ============================================================ #
        closure_result = close_april_snapshot(self.academic_year)

        self.assertTrue(closure_result, "close_april_snapshot must return True when all students are vetted.")

        remaining_unvetted = StudentState.objects.filter(
            academic_year=self.academic_year,
            student__is_active=True,
            vetting_status=VettingStatus.REQUIRES_REVIEW,
        ).count()
        self.assertEqual(remaining_unvetted, 0, "No unvetted students must remain after a successful closure.")


# ------------------------------------------------------------------ #
#  SUPPLEMENTARY: Snapshot Isolation                                   #
# ------------------------------------------------------------------ #

class Epic2SnapshotIsolationTest(TestCase):
    """
    Verifies that close_april_snapshot correctly scopes its gate query.
    Inactive students and different academic years must not block closure.
    """

    def setUp(self):
        self.academic_year = "2025-2026"

    def test_inactive_student_does_not_block_snapshot(self):
        """An inactive student with REQUIRES_REVIEW must not prevent closure."""
        inactive = Student.objects.create(
            fiche=6002,
            full_name="Étudiant Inactif",
            permanent_code="INA60020001",
            level="Sec 2",
            current_group="201",
            is_active=False,
        )
        StudentState.objects.create(
            student=inactive,
            academic_year=self.academic_year,
            vetting_status=VettingStatus.REQUIRES_REVIEW,
        )

        result = close_april_snapshot(self.academic_year)
        self.assertTrue(result)

    def test_prior_year_state_does_not_block_current_snapshot(self):
        """An unvetted state for a different academic year must not affect the current closure."""
        active = Student.objects.create(
            fiche=6003,
            full_name="Étudiant Autre Année",
            permanent_code="AUT60030001",
            level="Sec 3",
            current_group="301",
            is_active=True,
        )
        StudentState.objects.create(
            student=active,
            academic_year="2024-2025",  # prior year, not current
            vetting_status=VettingStatus.REQUIRES_REVIEW,
        )

        result = close_april_snapshot(self.academic_year)
        self.assertTrue(result)

    def test_mixed_vetting_statuses_block_only_when_requires_review_present(self):
        """
        Two active students: one AUTO_VETTED, one REQUIRES_REVIEW.
        Closure must be blocked, naming only the unvetted student.
        """
        vetted = Student.objects.create(
            fiche=6004,
            full_name="Étudiant Validé",
            permanent_code="VAL60040001",
            level="Sec 1",
            current_group="101",
            is_active=True,
        )
        StudentState.objects.create(
            student=vetted,
            academic_year=self.academic_year,
            vetting_status=VettingStatus.AUTO_VETTED,
        )

        pending = Student.objects.create(
            fiche=6005,
            full_name="Étudiant En Attente",
            permanent_code="ATT60050001",
            level="Sec 1",
            current_group="102",
            is_active=True,
        )
        StudentState.objects.create(
            student=pending,
            academic_year=self.academic_year,
            vetting_status=VettingStatus.REQUIRES_REVIEW,
        )

        with self.assertRaises(SnapshotClosureError) as cm:
            close_april_snapshot(self.academic_year)

        blocked_fiches = [s["fiche"] for s in cm.exception.incomplete_students]
        self.assertIn(pending.fiche, blocked_fiches)
        self.assertNotIn(vetted.fiche, blocked_fiches)


# ------------------------------------------------------------------ #
#  SUPPLEMENTARY: Guard Coverage Matrix                                #
# ------------------------------------------------------------------ #

class Epic2GuardCoverageTest(TestCase):
    """
    Verifies each US2.2 invariant independently via apply_event so that every
    guard rule is confirmed to be wired into the orchestration gateway.
    """

    def setUp(self):
        self.academic_year = "2025-2026"
        self.teacher = User.objects.create(email="teacher-guard@school.test")

        self.core_course = Course.objects.create(
            local_code="FRA-S1-E2",
            description="Français Secondaire 1 (Guard Tests)",
            is_core_or_sanctioned=True,
            level=1,
            credits=4,
        )
        self.offering = CourseOffering.objects.create(
            course=self.core_course,
            group_number="G2",
            academic_year=self.academic_year,
        )

    def _make_student(self, fiche: int, grade: int, workflow_state=None) -> Student:
        student = Student.objects.create(
            fiche=fiche,
            full_name=f"Étudiant Guard {fiche}",
            permanent_code=f"GRD{fiche:08d}",
            level="Sec 1",
            current_group="101",
            is_active=True,
        )
        StudentState.objects.create(
            student=student,
            academic_year=self.academic_year,
            workflow_state=workflow_state,
            vetting_status=VettingStatus.REQUIRES_REVIEW,
        )
        AcademicResult.objects.create(
            student=student,
            offering=self.offering,
            academic_year=self.academic_year,
            final_grade=grade,
        )
        return student

    def test_hard_blocker_guard_rejects_summer_routing(self):
        """
        Core course grade < 50 is a hard blocker.
        Routing to APRIL_FINAL_PROMOTE_WITH_SUMMER must be rejected.
        """
        student = self._make_student(fiche=7001, grade=45)

        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                student=student,
                academic_year=self.academic_year,
                event_name="ILLEGAL_SUMMER_HARD_BLOCK",
                new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_WITH_SUMMER,
                actor=self.teacher,
            )

        self.assertIn("hard blocker", str(cm.exception))

    def test_teacher_review_boundary_guard_rejects_sub_57_override(self):
        """
        A grade < 57 cannot be overridden to APRIL_FINAL_PROMOTE_REGULAR
        via teacher review. The boundary guard must block the attempt.
        """
        student = self._make_student(fiche=7002, grade=55)

        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                student=student,
                academic_year=self.academic_year,
                event_name="ILLEGAL_TEACHER_OVERRIDE_55",
                new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
                actor=self.teacher,
            )

        self.assertIn("Teacher review override not permitted", str(cm.exception))

    def test_ifp_prerequisite_guard_rejects_ifp_without_candidate_review(self):
        """
        A student not in IFP_CANDIDATE_REVIEW workflow cannot receive an IFP
        final outcome. The prerequisite guard must block the attempt.
        """
        # Student is in default/None workflow — NOT IFP_CANDIDATE_REVIEW
        student = self._make_student(fiche=7003, grade=40)

        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                student=student,
                academic_year=self.academic_year,
                event_name="ILLEGAL_IFP_ASSIGNMENT",
                new_final_april_state=FinalAprilState.APRIL_FINAL_IFP_N,
                actor=self.teacher,
            )

        self.assertIn("IFP_CANDIDATE_REVIEW", str(cm.exception))

    def test_de_finalization_guard_rejects_regression_to_pending(self):
        """
        Once a student has a final_april_state, the state machine must not
        allow regression back to REGULAR_REVIEW_PENDING (de-finalization).
        """
        student = self._make_student(fiche=7004, grade=72)

        # Legitimately finalise the student first
        apply_event(
            student=student,
            academic_year=self.academic_year,
            event_name="AUTO_PROMOTE_FINAL",
            new_final_april_state=FinalAprilState.APRIL_FINAL_PROMOTE_REGULAR,
            new_vetting_status=VettingStatus.AUTO_VETTED,
        )

        # Now attempt an illegal regression
        with self.assertRaises(IllegalTransitionError) as cm:
            apply_event(
                student=student,
                academic_year=self.academic_year,
                event_name="ILLEGAL_REGRESSION",
                new_workflow_state=WorkflowState.REGULAR_REVIEW_PENDING,
                actor=self.teacher,
            )

        self.assertIn("Cannot return to", str(cm.exception))
