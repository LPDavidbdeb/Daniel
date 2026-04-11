"""
Credit Classifier Service
=========================
Classifies student academic results for group projection purposes.

Two modes:
  - CLOSED groups (Sec 1-2, Zénith, IFP): one global outcome per student
  - OPEN groups (Sec 3-4-5 regular): one outcome per course, independently

The classifier is an indicator, not a decision system. Borderline cases are
surfaced for human review. Promotion criteria for some levels are stubs pending
confirmation of the business rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Protocol, runtime_checkable

from students.models import AcademicResult


# ---------------------------------------------------------------------------
# Core enumerations
# ---------------------------------------------------------------------------

class CourseClassification(str, Enum):
    CERTAIN_PASS    = "CERTAIN_PASS"    # grade >= 60  — credits earned
    TEACHER_REVIEW  = "TEACHER_REVIEW"  # 57 <= grade < 60 — teacher may bump
    BORDERLINE      = "BORDERLINE"      # 50 <= grade < 57 — summer school candidate
    CERTAIN_FAIL    = "CERTAIN_FAIL"    # grade < 50  — credits not earned
    NO_GRADE        = "NO_GRADE"        # grade is None — data not yet available


class PromotionOutcome(str, Enum):
    CERTAIN_PROMOTE = "CERTAIN_PROMOTE"
    BORDERLINE      = "BORDERLINE"      # requires human review
    CERTAIN_RETAIN  = "CERTAIN_RETAIN"


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class ClassifiedCourse:
    course_code: str
    description: str
    credits: int
    grade: Optional[int]
    classification: CourseClassification
    is_sanctioned: bool


@dataclass
class ClosedGroupOutcome:
    """Global promotion outcome for a student in a closed group."""
    student_fiche: int
    promotion_outcome: PromotionOutcome
    credits_floor: int            # credits certain (grade >= 60)
    credits_ceiling: int          # credits possible (grade >= 50)
    classified_courses: list[ClassifiedCourse]
    review_reason: Optional[str] = None
    warnings: list[str] = field(default_factory=list)  # additional flags that don't change the outcome
    criteria_stub: bool = False   # True when the strategy is not yet fully defined


@dataclass
class OpenGroupOutcome:
    """Per-course outcomes for a student in open groups (Sec 3-4-5)."""
    student_fiche: int
    classified_courses: list[ClassifiedCourse]

    @property
    def certain_pass(self) -> list[ClassifiedCourse]:
        return [c for c in self.classified_courses if c.classification == CourseClassification.CERTAIN_PASS]

    @property
    def needs_review(self) -> list[ClassifiedCourse]:
        return [c for c in self.classified_courses if c.classification in (
            CourseClassification.TEACHER_REVIEW, CourseClassification.BORDERLINE
        )]

    @property
    def certain_fail(self) -> list[ClassifiedCourse]:
        return [c for c in self.classified_courses if c.classification == CourseClassification.CERTAIN_FAIL]


# ---------------------------------------------------------------------------
# Promotion strategies (Strategy Pattern)
# ---------------------------------------------------------------------------

@runtime_checkable
class PromotionStrategy(Protocol):
    is_stub: bool

    def evaluate(
        self,
        credits_floor: int,
        credits_ceiling: int,
        classified_courses: list[ClassifiedCourse],
    ) -> tuple[PromotionOutcome, Optional[str], list[str]]:
        """Returns (outcome, review_reason, warnings)."""
        ...


class Sec1PromotionStrategy:
    """
    Sec 1 → Sec 2: no graduation criteria.
    All students advance automatically — no holdbacks, no summer school.
    This is the actual rule, not a stub.
    """
    is_stub = False

    def evaluate(self, credits_floor, credits_ceiling, classified_courses):
        return (
            PromotionOutcome.CERTAIN_PROMOTE,
            None,
            [],
        )


class Sec2PromotionStrategy:
    """
    Sec 2 → Sec 3 promotion.
    Primary gate: cumulative credits (Sec 1 + Sec 2) >= CREDIT_GATE.

    Additional flag (not a hard gate): if a student passed fewer than 2 of the
    3 core subjects (Français, Mathématique, Anglais), they are flagged for
    human review regardless of their credit total.
    Core subjects identified by MEQ code prefix (first 3 digits):
      132 = Français, 063 = Mathématique, 134 = Anglais
    """
    is_stub = False
    CREDIT_GATE = 52
    CORE_MEQ_PREFIXES = {"132", "063", "134"}
    CORE_PASS_MINIMUM = 2  # must have passed at least 2 of the 3 core subjects

    def evaluate(self, credits_floor, credits_ceiling, classified_courses):
        warnings = self._check_core_courses(classified_courses)
        core_ok = len(warnings) == 0

        if credits_floor >= self.CREDIT_GATE:
            if core_ok:
                # Hard pass: sufficient certain credits AND all core courses met
                return PromotionOutcome.CERTAIN_PROMOTE, None, []
            else:
                # Credits are there but core courses failed → teacher must review
                return (
                    PromotionOutcome.BORDERLINE,
                    "Crédits acquis mais matières de base insuffisantes",
                    warnings,
                )

        if credits_ceiling < self.CREDIT_GATE:
            return (
                PromotionOutcome.CERTAIN_RETAIN,
                f"Maximum atteignable {credits_ceiling} < {self.CREDIT_GATE} crédits requis",
                warnings,
            )

        credits_needed = self.CREDIT_GATE - credits_floor
        credits_in_play = credits_ceiling - credits_floor
        return (
            PromotionOutcome.BORDERLINE,
            f"Besoin de {credits_needed} crédit(s) supplémentaire(s) — {credits_in_play} en jeu (cours 50-59%)",
            warnings,
        )

    # Keywords to identify core subjects from course description (case-insensitive)
    CORE_DESCRIPTION_KEYWORDS = ("français", "mathematique", "anglais")

    def _check_core_courses(self, classified_courses: list[ClassifiedCourse]) -> list[str]:
        """Flag if fewer than CORE_PASS_MINIMUM core subjects are passed at >= 60."""
        core_results = [
            c for c in classified_courses
            if any(kw in c.description.lower() for kw in self.CORE_DESCRIPTION_KEYWORDS)
        ]
        core_passed = sum(
            1 for c in core_results
            if c.classification == CourseClassification.CERTAIN_PASS
        )
        if len(core_results) > 0 and core_passed < self.CORE_PASS_MINIMUM:
            failed_names = [
                c.description for c in core_results
                if c.classification != CourseClassification.CERTAIN_PASS
            ]
            return [
                f"Matières de base insuffisantes : {core_passed}/{len(core_results)} réussies "
                f"(minimum {self.CORE_PASS_MINIMUM}) — {', '.join(failed_names)}"
            ]
        return []


class Sec5DiplomaStrategy:
    """
    Sec 5 diplomation.
    STUB — credit threshold and sanctioned course list TBD.
    Default assumption: CERTAIN_PROMOTE (everyone graduates unless proven otherwise).
    """
    is_stub = True
    # CREDIT_GATE: int = ?                   # TODO
    # SANCTIONED_MEQ_CODES: list[str] = []   # TODO: e.g. Histoire Sec 4

    def evaluate(self, credits_floor, credits_ceiling, classified_courses):
        return (
            PromotionOutcome.CERTAIN_PROMOTE,
            None,
            [],
        )


class IFPPromotionStrategy:
    """
    IFP cohort — closed group, promotion criteria TBD.
    Default assumption: CERTAIN_PROMOTE.
    STUB.
    """
    is_stub = True

    def evaluate(self, credits_floor, credits_ceiling, classified_courses):
        return (
            PromotionOutcome.CERTAIN_PROMOTE,
            None,
            [],
        )


class ZenithPromotionStrategy(Sec2PromotionStrategy):
    """
    Zénith — closed group, follows same credit gate as Sec 1-2 for now.
    If the Zénith group falls below viability, dissolution into REGULAR
    is handled at the projection level, not here.
    """
    is_stub = False


# Maps (student.level, course stream) → strategy instance
_STRATEGY_MAP: dict[tuple[str, str], PromotionStrategy] = {
    ("1", "REGULAR"): Sec1PromotionStrategy(),
    ("1", "ZENITH"):  Sec1PromotionStrategy(),
    ("2", "REGULAR"): Sec2PromotionStrategy(),
    ("2", "ZENITH"):  ZenithPromotionStrategy(),
    ("5", "REGULAR"): Sec5DiplomaStrategy(),
    ("IFP", "IFP"):   IFPPromotionStrategy(),
}

_FALLBACK_STRATEGY = Sec1PromotionStrategy()  # stub for anything unexpected


# ---------------------------------------------------------------------------
# Main classifier service
# ---------------------------------------------------------------------------

class CreditClassifierService:

    # Grade thresholds
    PASS_THRESHOLD          = 60
    TEACHER_REVIEW_THRESHOLD = 57
    BORDERLINE_THRESHOLD    = 50

    # ---------------------------------------------------------------------------
    # Atomic classification
    # ---------------------------------------------------------------------------

    @classmethod
    def classify_grade(cls, grade: Optional[int]) -> CourseClassification:
        if grade is None:
            return CourseClassification.NO_GRADE
        if grade >= cls.PASS_THRESHOLD:
            return CourseClassification.CERTAIN_PASS
        if grade >= cls.TEACHER_REVIEW_THRESHOLD:
            return CourseClassification.TEACHER_REVIEW
        if grade >= cls.BORDERLINE_THRESHOLD:
            return CourseClassification.BORDERLINE
        return CourseClassification.CERTAIN_FAIL

    # ---------------------------------------------------------------------------
    # Open group classification (Sec 3-4-5 REGULAR)
    # ---------------------------------------------------------------------------

    @classmethod
    def classify_open_group_student(
        cls,
        student,
        academic_year: str,
    ) -> OpenGroupOutcome:
        results = (
            AcademicResult.objects
            .filter(
                student=student,
                academic_year=academic_year,
                offering__course__group_type="OPEN",
            )
            .select_related("offering__course")
        )

        classified = [
            ClassifiedCourse(
                course_code=r.offering.course.local_code,
                description=r.offering.course.description,
                credits=r.offering.course.credits,
                grade=r.final_grade,
                classification=cls.classify_grade(r.final_grade),
                is_sanctioned=r.offering.course.is_core_or_sanctioned,
            )
            for r in results
        ]

        return OpenGroupOutcome(
            student_fiche=student.fiche,
            classified_courses=classified,
        )

    # ---------------------------------------------------------------------------
    # Closed group classification (Sec 1-2, Zénith, IFP)
    # ---------------------------------------------------------------------------

    @classmethod
    def classify_closed_group_student(
        cls,
        student,
        academic_year: str,
        include_year_from: Optional[str] = None,
    ) -> ClosedGroupOutcome:
        """
        include_year_from: if set, accumulates credits from that year onwards
        (used for Sec 2 students who need cumulative Sec 1 + Sec 2 credits).
        """
        qs = (
            AcademicResult.objects
            .filter(
                student=student,
                offering__course__group_type="CLOSED",
            )
            .select_related("offering__course")
        )

        if include_year_from:
            qs = qs.filter(
                academic_year__gte=include_year_from,
                academic_year__lte=academic_year,
            )
        else:
            qs = qs.filter(academic_year=academic_year)

        classified = [
            ClassifiedCourse(
                course_code=r.offering.course.local_code,
                description=r.offering.course.description,
                credits=r.offering.course.credits,
                grade=r.final_grade,
                classification=cls.classify_grade(r.final_grade),
                is_sanctioned=r.offering.course.is_core_or_sanctioned,
            )
            for r in qs
        ]

        credits_floor = sum(
            c.credits for c in classified
            if c.classification == CourseClassification.CERTAIN_PASS
        )
        credits_ceiling = sum(
            c.credits for c in classified
            if c.classification in (
                CourseClassification.CERTAIN_PASS,
                CourseClassification.TEACHER_REVIEW,
                CourseClassification.BORDERLINE,
            )
        )

        # Determine stream from the student's enrolled courses
        streams = {c.course_code[:3] for c in classified}  # rough heuristic
        enrolled_streams = (
            AcademicResult.objects
            .filter(student=student, academic_year=academic_year)
            .values_list("offering__course__stream", flat=True)
            .distinct()
        )
        primary_stream = next(
            (s for s in enrolled_streams if s in ("ZENITH", "IFP", "ACCUEIL")),
            "REGULAR",
        )

        strategy = _STRATEGY_MAP.get(
            (str(student.level), primary_stream),
            _FALLBACK_STRATEGY,
        )
        outcome, reason, warnings = strategy.evaluate(credits_floor, credits_ceiling, classified)

        return ClosedGroupOutcome(
            student_fiche=student.fiche,
            promotion_outcome=outcome,
            credits_floor=credits_floor,
            credits_ceiling=credits_ceiling,
            classified_courses=classified,
            review_reason=reason,
            warnings=warnings,
            criteria_stub=strategy.is_stub,
        )
