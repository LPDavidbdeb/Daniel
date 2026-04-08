from ninja import ModelSchema, Schema
from typing import List, Optional
from .models import Student, AcademicResult

class AcademicResultOut(ModelSchema):
    class Meta:
        model = AcademicResult
        fields = ['course_code', 'course_description', 'course_group', 'teacher_name', 'step_1_grade', 'step_2_grade', 'final_grade']

class StudentOut(ModelSchema):
    class Meta:
        model = Student
        fields = ['fiche', 'permanent_code', 'full_name', 'level', 'current_group', 'is_active']

class StudentDetailOut(StudentOut):
    results: List[AcademicResultOut]

class GroupListOut(Schema):
    group_name: str
    student_count: int
