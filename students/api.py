from typing import List
from django.db.models import Count
from django.shortcuts import get_object_or_404
from ninja import Router
from .models import Student
from .schemas import StudentOut, StudentDetailOut, GroupListOut

router = Router()

@router.get("/groups", response=List[GroupListOut])
def list_groups(request):
    groups = Student.objects.filter(is_active=True).values('current_group').annotate(student_count=Count('fiche')).order_by('current_group')
    return [{"group_name": g['current_group'], "student_count": g['student_count']} for g in groups]

@router.get("/groups/{group_name}/students", response=List[StudentDetailOut])
def list_group_students(request, group_name: str):
    # On décode le nom du groupe car il peut contenir des caractères spéciaux (espaces, etc.)
    return Student.objects.filter(current_group=group_name, is_active=True).prefetch_related('results')

@router.get("/{fiche}", response=StudentDetailOut)
def get_student_detail(request, fiche: int):
    return get_object_or_404(Student, fiche=fiche)
