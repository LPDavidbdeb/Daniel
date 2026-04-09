from ninja import ModelSchema, Schema
from typing import List, Optional
from .models import Course, Teacher, CourseOffering

class CourseCrudIn(Schema):
    local_code: str
    meq_code: Optional[str] = None
    description: str
    level: Optional[int] = None
    credits: int = 0
    periods: int = 0
    is_core_or_sanctioned: bool = False
    is_active: bool = True

class CourseCrudOut(ModelSchema):
    class Meta:
        model = Course
        fields = ['id', 'local_code', 'meq_code', 'description', 'level', 'credits', 'periods', 'is_core_or_sanctioned', 'is_active']

class TeacherCrudIn(Schema):
    user: int  # ID
    full_name: str
    is_active: bool = True

class TeacherCrudOut(ModelSchema):
    user_email: str

    class Meta:
        model = Teacher
        fields = ['id', 'user', 'full_name', 'is_active']

    @staticmethod
    def resolve_user_email(obj):
        return obj.user.email

class CourseOfferingCrudIn(Schema):
    course: int  # ID
    group_number: str
    academic_year: str
    teacher: Optional[int] = None  # ID
    is_active: bool = True

class CourseOfferingCrudOut(ModelSchema):
    class Meta:
        model = CourseOffering
        fields = ['id', 'course', 'group_number', 'academic_year', 'teacher', 'is_active']

class StudentMinimalOut(Schema):
    fiche: int
    full_name: str

class ResultForTeacherOut(Schema):
    student: StudentMinimalOut
    step_1_grade: Optional[int] = None
    step_2_grade: Optional[int] = None
    final_grade: Optional[int] = None

class OfferingDetailOut(Schema):
    id: int
    course_local_code: str
    course_description: str
    group_number: str
    results: List[ResultForTeacherOut]

class TeacherDetailOut(Schema):
    id: int
    full_name: str
    email: str
    offerings: List[OfferingDetailOut]
