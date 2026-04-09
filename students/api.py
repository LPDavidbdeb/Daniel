from typing import List, Dict, Any, Optional
import urllib.parse
from django.db.models import Count, Q, Avg
from django.db.models.functions import Substr
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from .models import Student, AcademicResult
from .schemas import StudentOut, StudentDetailOut, GroupListOut

router = Router()

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
            for student in students_in_lvl:
                # On récupère les notes finales des matières de base
                core_fails = student.results.filter(
                    Q(offering__course__description__icontains="FRANCAIS") |
                    Q(offering__course__description__icontains="MATHEMATIQUE") |
                    Q(offering__course__description__icontains="ANGLAIS"),
                    final_grade__lt=50
                ).count()
                
                if core_fails >= 2:
                    at_risk_ids.append(student.fiche)
            
            stat_item["at_risk_count"] = len(at_risk_ids)
        
        else:
            # --- LOGIQUE 2e CYCLE (PAR MATIÈRE) ---
            course_data = AcademicResult.objects.filter(student__in=students_in_lvl) \
                .values('offering__course__local_code', 'offering__course__description') \
                .annotate(student_count=Count('student_id', distinct=True)) \
                .order_by('offering__course__local_code')
            
            stat_item["course_stats"] = [
                {
                    "code": c['offering__course__local_code'],
                    "description": c['offering__course__description'],
                    "count": c['student_count']
                } for c in course_data
            ]

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

@router.get("/{fiche}", response=StudentDetailOut)
def get_student_detail(request, fiche: int):
    return get_object_or_404(Student, fiche=fiche)
