from ninja import ModelSchema, Schema
from typing import List, Optional

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
    course_code: str
    course_description: str
    group_number: str
    results: List[ResultForTeacherOut]

class TeacherDetailOut(Schema):
    id: int
    full_name: str
    email: str
    offerings: List[OfferingDetailOut]
