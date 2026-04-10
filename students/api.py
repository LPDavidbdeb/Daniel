from typing import List, Dict, Any, Optional
import urllib.parse
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth
from .models import Student, AcademicResult
from .schemas import StudentDetailOut, GroupListOut, StudentCrudIn, StudentCrudOut, EvaluationOut
from .services import StudentProfilingService, StudentEvaluator

router = Router(auth=JWTAuth())

def _require_superuser(request) -> None:
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or not user.is_superuser:
        raise HttpError(403, 'Acces refuse: superuser requis.')

class LevelStatOut(Schema):
    level: str
    total_students: int
    at_risk_count: Optional[int] = None  # Pour Sec 1 et 2
    course_stats: Optional[List[Dict[str, Any]]] = None  # Pour Sec 3, 4, 5

@router.get("/stats/summary", response=List[LevelStatOut])
def get_stats_summary(request):
    levels = ["1", "2", "3", "4", "5"]
    results = []

    for lvl in levels:
        # 1. Total d'élèves par niveau
        students_in_lvl = Student.objects.filter(is_active=True, current_group__startswith=lvl)
        total_count = students_in_lvl.count()
        
        if total_count == 0: continue

        stat_item = {"level": lvl, "total_students": total_count}

        if lvl in ["1", "2"]:
            # --- LOGIQUE 1er CYCLE (RÉVISION GLOBALE) ---
            # Un élève est "à risque" s'il a < 50 dans au moins 2 matières de base (Français, Math, Anglais)
            
            at_risk_ids = []
            core_course_filter = (
                Q(offering__course__description__icontains="FRANCAIS") |
                Q(offering__course__description__icontains="MATHEMATIQUE") |
                Q(offering__course__description__icontains="ANGLAIS")
            )
            for student in students_in_lvl:
                # On récupère les notes finales des matières de base
                core_fails = AcademicResult.objects.filter(
                    student=student,
                    final_grade__lt=50
                ).filter(core_course_filter).count()

                if core_fails >= 2:
                    at_risk_ids.append(student.fiche)
            
            stat_item["at_risk_count"] = len(at_risk_ids)
        
        else:
            # --- LOGIQUE 2e CYCLE (PAR MATIÈRE) ---
            course_data = AcademicResult.objects.filter(student__in=students_in_lvl) \
                .values('offering__course__local_code', 'offering__course__description') \
                .annotate(student_count=Count('student_id', distinct=True)) \
                .order_by('offering__course__local_code')
            
            course_stats = [
                {
                    "code": c['offering__course__local_code'],
                    "description": c['offering__course__description'],
                    "count": c['student_count']
                } for c in course_data
            ]
            stat_item["course_stats"] = course_stats

        results.append(stat_item)
    
    return results

# ... (reste des endpoints existants)
@router.get("/groups", response=List[GroupListOut])
def list_groups(request):
    groups = Student.objects.filter(is_active=True).values('current_group').annotate(student_count=Count('fiche')).order_by('current_group')
    return [{"group_name": g['current_group'], "student_count": g['student_count']} for g in groups]

@router.get("/groups/{group_name}/students", response=List[StudentDetailOut])
def list_group_students(request, group_name: str):
    decoded_name = urllib.parse.unquote(group_name)
    return Student.objects.filter(current_group=decoded_name, is_active=True).prefetch_related('results__offering__course','results__offering__teacher')


@router.get("/{fiche}/evaluation", response=EvaluationOut)
def get_student_evaluation(request, fiche: int, year: Optional[str] = "2024-2025"):
    student = get_object_or_404(Student, fiche=fiche)
    return StudentEvaluator.evaluate_student_year(student, year)


@router.get("/{fiche}", response=StudentDetailOut)
def get_student_detail(request, fiche: int):
    return get_object_or_404(Student, fiche=fiche)


@router.get('/crud/students', response=List[StudentCrudOut])
def list_students_crud(request):
    _require_superuser(request)
    return Student.objects.all().order_by('full_name')


@router.post('/crud/students', response=StudentCrudOut)
def create_student_crud(request, payload: StudentCrudIn):
    _require_superuser(request)
    try:
        return Student.objects.create(
            fiche=payload.fiche,
            permanent_code=payload.permanent_code,
            full_name=payload.full_name,
            level=payload.level,
            current_group=payload.current_group,
            is_active=payload.is_active,
        )
    except IntegrityError:
        raise HttpError(409, 'Conflit: fiche ou code permanent deja utilise.')


@router.put('/crud/students/{fiche}', response=StudentCrudOut)
def update_student_crud(request, fiche: int, payload: StudentCrudIn):
    _require_superuser(request)
    if payload.fiche != fiche:
        raise HttpError(400, 'La fiche du formulaire doit correspondre a la ressource.')

    student = get_object_or_404(Student, fiche=fiche)
    student.permanent_code = payload.permanent_code
    student.full_name = payload.full_name
    student.level = payload.level
    student.current_group = payload.current_group
    student.is_active = payload.is_active
    try:
        student.save()
    except IntegrityError:
        raise HttpError(409, 'Conflit: code permanent deja utilise.')
    return student


@router.delete('/crud/students/{fiche}')
def delete_student_crud(request, fiche: int):
    _require_superuser(request)
    student = get_object_or_404(Student, fiche=fiche)
    student.delete()
    return {'ok': True}
