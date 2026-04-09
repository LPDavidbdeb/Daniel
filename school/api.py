from typing import List
from django.shortcuts import get_object_or_404
from ninja import Router
from .models import Teacher
from .schemas import TeacherDetailOut

router = Router()

@router.get("/teachers", response=List[TeacherDetailOut])
def list_teachers(request):
    teachers = Teacher.objects.filter(is_active=True).prefetch_related('offerings__course', 'user')
    
    results = []
    for teacher in teachers:
        offerings_data = []
        for offering in teacher.offerings.all():
            offerings_data.append({
                "id": offering.id,
                "course_code": offering.course.code,
                "course_description": offering.course.description,
                "group_number": offering.group_number,
                "results": [] # On ne charge pas les élèves dans la liste globale pour la performance
            })
        
        results.append({
            "id": teacher.id,
            "full_name": teacher.full_name,
            "email": teacher.user.email if teacher.user else "N/A",
            "offerings": offerings_data
        })
    return results

@router.get("/{teacher_id}", response=TeacherDetailOut)
def get_teacher_detail(request, teacher_id: int):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    offerings_data = []
    for offering in teacher.offerings.all().prefetch_related('results__student', 'course'):
        offerings_data.append({
            "id": offering.id,
            "course_code": offering.course.code,
            "course_description": offering.course.description,
            "group_number": offering.group_number,
            "results": [
                {
                    "student": {"fiche": r.student.fiche, "full_name": r.student.full_name},
                    "step_1_grade": r.step_1_grade,
                    "step_2_grade": r.step_2_grade,
                    "final_grade": r.final_grade
                } for r in offering.results.all()
            ]
        })
    return {
        "id": teacher.id,
        "full_name": teacher.full_name,
        "email": teacher.user.email if teacher.user else "N/A",
        "offerings": offerings_data
    }
