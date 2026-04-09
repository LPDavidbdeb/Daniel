from ninja import ModelSchema, Schema
from typing import List, Optional
from .models import Student, AcademicResult
from .services import StudentProfilingService

class AcademicResultOut(Schema):
    course_local_code: str
    course_description: str
    course_group: str
    teacher_name: Optional[str] = None
    teacher_id: Optional[int] = None
    step_1_grade: Optional[int] = None
    step_2_grade: Optional[int] = None
    final_grade: Optional[int] = None

    @staticmethod
    def resolve_course_local_code(obj):
        return obj.offering.course.local_code if obj.offering else "N/A"

    @staticmethod
    def resolve_course_description(obj):
        return obj.offering.course.description if obj.offering else "N/A"

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

class StudentCrudIn(Schema):
    fiche: int
    permanent_code: str
    full_name: str
    level: str
    current_group: str
    is_active: bool = True


class StudentCrudOut(ModelSchema):
    class Meta:
        model = Student
        fields = ['fiche', 'permanent_code', 'full_name', 'level', 'current_group', 'is_active']
