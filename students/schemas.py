from ninja import ModelSchema, Schema
from typing import List, Optional, Literal
from .models import Student
from .enums import VettingStatus
from .services import StudentProfilingService


def _resolve_vetting_status(obj) -> Optional[str]:
    # Prefer API-prefetched state to avoid per-row DB queries on list endpoints.
    prefetched_states = getattr(obj, 'active_year_states', None)
    if prefetched_states is not None:
        return prefetched_states[0].vetting_status if prefetched_states else None

    latest_state = obj.states.order_by('-academic_year').first()
    return latest_state.vetting_status if latest_state else None

class AcademicResultOut(Schema):
    course_code: str
    course_description: str
    course_group: str
    teacher_name: Optional[str] = None
    teacher_id: Optional[int] = None
    step_1_grade: Optional[int] = None
    step_2_grade: Optional[int] = None
    final_grade: Optional[int] = None

    @staticmethod
    def resolve_course_code(obj):
        if obj.offering and obj.offering.course:
            return obj.offering.course.local_code
        return "N/A"

    @staticmethod
    def resolve_course_description(obj):
        if obj.offering and obj.offering.course:
            return obj.offering.course.description
        return "N/A"

    @staticmethod
    def resolve_course_group(obj):
        return obj.offering.group_number if obj.offering else "N/A"

    @staticmethod
    def resolve_teacher_name(obj):
        if obj.offering and obj.offering.teacher:
            return obj.offering.teacher.full_name
        return None

    @staticmethod
    def resolve_teacher_id(obj):
        if obj.offering and obj.offering.teacher:
            return obj.offering.teacher.id
        return None

class StudentOut(ModelSchema):
    average: Optional[float] = None
    failed_courses_count: int = 0
    academic_profile: str = "Non évalué"
    sanctioned_passed_count: int = 0
    vetting_status: Optional[Literal[
        VettingStatus.AUTO_VETTED,
        VettingStatus.REQUIRES_REVIEW,
        VettingStatus.MANUALLY_VETTED,
    ]] = None

    class Meta:
        model = Student
        fields = ['fiche', 'permanent_code', 'full_name', 'level', 'current_group', 'is_active']

    @staticmethod
    def resolve_average(obj):
        return StudentProfilingService.calculate_student_average(obj)

    @staticmethod
    def resolve_failed_courses_count(obj):
        return len(StudentProfilingService.get_failed_courses(obj))

    @staticmethod
    def resolve_academic_profile(obj):
        return StudentProfilingService.determine_academic_profile(obj)

    @staticmethod
    def resolve_sanctioned_passed_count(obj):
        return StudentProfilingService.count_sanctioned_passed(obj)

    @staticmethod
    def resolve_vetting_status(obj):
        return _resolve_vetting_status(obj)

class StudentQueueOut(StudentOut):
    workflow_state: Optional[str] = None
    reason_codes: dict = {}
    results: List[AcademicResultOut] = []

    @staticmethod
    def resolve_workflow_state(obj):
        prefetched_states = getattr(obj, 'active_year_states', None)
        if prefetched_states:
            return prefetched_states[0].workflow_state
        return None

    @staticmethod
    def resolve_reason_codes(obj):
        prefetched_states = getattr(obj, 'active_year_states', None)
        if prefetched_states:
            return prefetched_states[0].reason_codes
        return {}

    @staticmethod
    def resolve_results(obj):
        return getattr(obj, 'active_year_results', [])

class StudentDetailOut(StudentOut):
    results: List[AcademicResultOut] = []

class GroupListOut(Schema):
    group_name: str
    student_count: int

class YearStatsOut(Schema):
    year: str
    student_count: int

class LevelCourseStatOut(Schema):
    level: str
    course_code: str
    course_description: str
    student_count: int

class LevelProjectionOut(Schema):
    level: str
    current_count: int
    certain_promote: int
    borderline: int
    certain_retain: int
    zenith_count: int
    ifp_count: int
    criteria_stub: bool
    target_size: int

class GroupProjectionOut(Schema):
    group_name: str
    stream: str          # REGULAR, ZENITH, IFP, ACCUEIL, DIM, OTHER
    student_count: int
    certain_promote: int
    borderline: int
    certain_retain: int
    criteria_stub: bool

class ClassifiedCourseOut(Schema):
    course_code: str
    description: str
    credits: int
    grade: Optional[int]
    classification: str
    is_sanctioned: bool

class StudentProjectionOut(Schema):
    fiche: int
    full_name: str
    current_group: str
    promotion_outcome: Optional[str] = None   # closed groups only
    review_reason: Optional[str] = None
    warnings: List[str] = []
    criteria_stub: bool = False
    classified_courses: List[ClassifiedCourseOut] = []

class CourseProjectionOut(Schema):
    course_code: str
    description: str
    credits: int
    is_sanctioned: bool
    student_count: int
    certain_pass: int
    teacher_review: int
    borderline: int
    certain_fail: int
    no_grade: int

class CourseStudentOut(Schema):
    fiche: int
    full_name: str
    current_group: str
    grade: Optional[int]
    classification: str
    courses_below_60: int
    courses_below_50: int
    courses_below_60_list: List[str]   # "Description (grade)" for tooltip
    courses_below_50_list: List[str]
    summer_school_enrollment_id: Optional[int] = None
    summer_school_course_code: Optional[str] = None
    summer_school_course_desc: Optional[str] = None


class SummerSchoolEnrollIn(Schema):
    student_fiche: int
    course_code: str
    academic_year: str


class SummerSchoolEnrollOut(Schema):
    id: int
    student_fiche: int
    student_name: str
    course_code: str
    course_desc: str
    academic_year: str
    enrolled_at: str


class EvaluationActionIn(Schema):
    academic_year: str
    action: Literal['MANUAL_VETTING', 'RESOLVE_REVIEW']
    course_code: Optional[str] = None
    override_type: Optional[str] = None
    reason: Optional[str] = None
    new_workflow_state: Optional[str] = None
    new_final_april_state: Optional[str] = None

class StudentCrudIn(Schema):
    fiche: int
    permanent_code: str
    full_name: str
    level: str
    current_group: str
    is_active: bool = True


class StudentCrudOut(ModelSchema):
    vetting_status: Optional[Literal[
        VettingStatus.AUTO_VETTED,
        VettingStatus.REQUIRES_REVIEW,
        VettingStatus.MANUALLY_VETTED,
    ]] = None

    class Meta:
        model = Student
        fields = ['fiche', 'permanent_code', 'full_name', 'level', 'current_group', 'is_active']

    @staticmethod
    def resolve_vetting_status(obj):
        return _resolve_vetting_status(obj)

class EvaluationOut(Schema):
    student_id: int
    academic_year: str
    total_credits_accumulated: int
    potentiel_minimum: int
    potentiel_maximum: int
    credits_en_jeu: int
    core_failures_count: int
    borderline_count: int
    recommendation: str
    confidence: str
    requires_review: bool


class TriageMatrixItem(Schema):
    total_failures: int
    core_failures: int
    student_count: int


class TriageDrilldownOut(Schema):
    subject: str
    grade_band: str
    failure_count: int
