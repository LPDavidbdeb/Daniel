from typing import List, Dict, Any, Optional
import urllib.parse
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth
from .models import Student, AcademicResult, SummerSchoolEnrollment
from .schemas import (
    StudentDetailOut, GroupListOut, StudentCrudIn, StudentCrudOut, EvaluationOut,
    LevelProjectionOut, GroupProjectionOut, StudentProjectionOut, ClassifiedCourseOut,
    CourseProjectionOut, CourseStudentOut, SummerSchoolEnrollIn, SummerSchoolEnrollOut,
)
from .services import StudentProfilingService, StudentEvaluator
from .services.classifier import CreditClassifierService, PromotionOutcome

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

TARGET_GROUP_SIZE: dict[str, int] = {
    '1': 28,
    '2': 29,
    '3': 32,
    '4': 32,
    '5': 32,
}


def _stream_for_group(group_name: str) -> str:
    """Infer stream from group naming convention."""
    g = group_name.upper()
    if g.endswith('30'):
        return 'ZENITH'
    if g.startswith('P') and g[1:].isdigit():
        return 'IFP'
    if g.startswith('S') and g[1:].isdigit():
        return 'ACCUEIL'
    if g.startswith('D') and g[1:].isdigit():
        return 'DIM'
    return 'REGULAR'


def _classify_students_for_level(students, academic_year: str, level: str):
    """
    Bulk-classify students at a given level.
    Returns (certain_promote, borderline, certain_retain, criteria_stub).
    For open groups (Sec 3-5), everyone counts as certain_promote (no level retention).
    """
    if level not in ('1', '2'):
        return students.count(), 0, 0, False

    include_from = '2024-2025' if level == '2' else None
    certain_promote = borderline = certain_retain = 0
    criteria_stub = False

    prefetched = students.prefetch_related('results__offering__course', 'overrides')
    for student in prefetched:
        outcome = CreditClassifierService.classify_closed_group_student(
            student, academic_year, include_year_from=include_from
        )
        if outcome.criteria_stub:
            criteria_stub = True
        if outcome.promotion_outcome == PromotionOutcome.CERTAIN_PROMOTE:
            certain_promote += 1
        elif outcome.promotion_outcome == PromotionOutcome.BORDERLINE:
            borderline += 1
        else:
            certain_retain += 1

    return certain_promote, borderline, certain_retain, criteria_stub


@router.get("/projection/summary", response=List[LevelProjectionOut])
def get_projection_summary(request, year: str = "2025-2026"):
    result = []
    for level in ("1", "2", "3", "4", "5"):
        students = Student.objects.filter(is_active=True, level=level)
        total = students.count()
        if total == 0:
            continue

        certain_promote, borderline, certain_retain, criteria_stub = \
            _classify_students_for_level(students, year, level)

        # Identify Zénith and IFP students via course enrollment
        zenith_count = AcademicResult.objects.filter(
            student__in=students,
            academic_year=year,
            offering__course__stream='ZENITH',
        ).values('student_id').distinct().count()

        ifp_count = AcademicResult.objects.filter(
            student__in=students,
            academic_year=year,
            offering__course__stream='IFP',
        ).values('student_id').distinct().count()

        result.append({
            'level': level,
            'current_count': total,
            'certain_promote': certain_promote,
            'borderline': borderline,
            'certain_retain': certain_retain,
            'zenith_count': zenith_count,
            'ifp_count': ifp_count,
            'criteria_stub': criteria_stub,
            'target_size': TARGET_GROUP_SIZE.get(level, 32),
        })
    return result


@router.get("/projection/{level}/groups", response=List[GroupProjectionOut])
def get_projection_groups(request, level: str, year: str = "2025-2026"):
    students_qs = Student.objects.filter(is_active=True, level=level)
    groups = students_qs.values('current_group').annotate(n=Count('fiche')).order_by('current_group')

    include_from = '2024-2025' if level == '2' else None
    result = []

    for g in groups:
        group_name = g['current_group']
        stream = _stream_for_group(group_name)
        group_students = students_qs.filter(current_group=group_name)

        certain_promote, borderline, certain_retain, criteria_stub = \
            _classify_students_for_level(group_students, year, level)

        result.append({
            'group_name': group_name,
            'stream': stream,
            'student_count': g['n'],
            'certain_promote': certain_promote,
            'borderline': borderline,
            'certain_retain': certain_retain,
            'criteria_stub': criteria_stub,
        })
    return result


@router.get("/projection/{level}/{group}/students", response=List[StudentProjectionOut])
def get_projection_students(request, level: str, group: str, year: str = "2025-2026"):
    decoded_group = urllib.parse.unquote(group)
    students = Student.objects.filter(
        is_active=True, level=level, current_group=decoded_group
    ).prefetch_related('results__offering__course', 'overrides')

    include_from = '2024-2025' if level == '2' else None
    is_closed = level in ('1', '2')
    result = []

    for student in students:
        if is_closed:
            outcome = CreditClassifierService.classify_closed_group_student(
                student, year, include_year_from=include_from
            )
            classified_courses = [
                ClassifiedCourseOut(
                    course_code=c.course_code,
                    description=c.description,
                    credits=c.credits,
                    grade=c.grade,
                    classification=c.classification.value,
                    is_sanctioned=c.is_sanctioned,
                )
                for c in outcome.classified_courses
            ]
            result.append({
                'fiche': student.fiche,
                'full_name': student.full_name,
                'current_group': student.current_group,
                'promotion_outcome': outcome.promotion_outcome.value,
                'review_reason': outcome.review_reason,
                'warnings': outcome.warnings,
                'criteria_stub': outcome.criteria_stub,
                'classified_courses': classified_courses,
            })
        else:
            outcome = CreditClassifierService.classify_open_group_student(student, year)
            classified_courses = [
                ClassifiedCourseOut(
                    course_code=c.course_code,
                    description=c.description,
                    credits=c.credits,
                    grade=c.grade,
                    classification=c.classification.value,
                    is_sanctioned=c.is_sanctioned,
                )
                for c in outcome.classified_courses
            ]
            result.append({
                'fiche': student.fiche,
                'full_name': student.full_name,
                'current_group': student.current_group,
                'promotion_outcome': None,
                'review_reason': None,
                'warnings': [],
                'criteria_stub': False,
                'classified_courses': classified_courses,
            })
    return result


@router.get("/projection/{level}/courses", response=List[CourseProjectionOut])
def get_projection_courses(request, level: str, year: str = "2025-2026"):
    from school.models import Course
    courses = (
        Course.objects
        .filter(level=int(level), group_type="OPEN", is_active=True)
        .order_by('local_code')
    )
    result = []
    for course in courses:
        qs = AcademicResult.objects.filter(
            offering__course=course,
            academic_year=year,
        )
        total = qs.count()
        if total == 0:
            continue
        result.append(CourseProjectionOut(
            course_code=course.local_code,
            description=course.description,
            credits=course.credits,
            is_sanctioned=course.is_core_or_sanctioned,
            student_count=total,
            certain_pass=qs.filter(final_grade__gte=60).count(),
            teacher_review=qs.filter(final_grade__gte=57, final_grade__lt=60).count(),
            borderline=qs.filter(final_grade__gte=50, final_grade__lt=57).count(),
            certain_fail=qs.filter(final_grade__isnull=False, final_grade__lt=50).count(),
            no_grade=qs.filter(final_grade__isnull=True).count(),
        ))
    return result


@router.get("/projection/{level}/courses/{course_code}/students", response=List[CourseStudentOut])
def get_projection_course_students(request, level: str, course_code: str, year: str = "2025-2026"):
    results = (
        AcademicResult.objects
        .filter(
            offering__course__local_code=course_code,
            offering__course__level=int(level),
            academic_year=year,
        )
        .select_related('student', 'offering__course')
        .order_by('student__full_name')
    )
    # Bulk-fetch enrollments for all students in one query
    student_ids = [r.student_id for r in results]
    enrollments = {
        e.student_id: e
        for e in SummerSchoolEnrollment.objects.filter(
            student_id__in=student_ids,
            academic_year=year,
        ).select_related('course')
    }

    rows = []
    for r in results:
        all_results = list(
            AcademicResult.objects.filter(
                student=r.student,
                academic_year=year,
                final_grade__isnull=False,
            ).select_related('offering__course')
        )
        below_60 = [a for a in all_results if a.final_grade < 60]
        below_50 = [a for a in all_results if a.final_grade < 50]
        enroll = enrollments.get(r.student_id)
        rows.append(CourseStudentOut(
            fiche=r.student.fiche,
            full_name=r.student.full_name,
            current_group=r.student.current_group,
            grade=r.final_grade,
            classification=CreditClassifierService.classify_grade(r.final_grade).value,
            courses_below_60=len(below_60),
            courses_below_50=len(below_50),
            courses_below_60_list=[
                f"{a.offering.course.description} ({a.final_grade})" for a in below_60
            ],
            courses_below_50_list=[
                f"{a.offering.course.description} ({a.final_grade})" for a in below_50
            ],
            summer_school_enrollment_id=enroll.id if enroll else None,
            summer_school_course_code=enroll.course.local_code if enroll else None,
            summer_school_course_desc=enroll.course.description if enroll else None,
        ))
    return rows


@router.post("/summer-school/enroll", response=SummerSchoolEnrollOut)
def summer_school_enroll(request, payload: SummerSchoolEnrollIn):
    from school.models import Course
    student = get_object_or_404(Student, fiche=payload.student_fiche)
    course = get_object_or_404(Course, local_code=payload.course_code)
    try:
        enroll = SummerSchoolEnrollment.objects.create(
            student=student,
            course=course,
            academic_year=payload.academic_year,
            enrolled_by=request.user,
        )
    except IntegrityError:
        raise HttpError(409, 'Cet élève est déjà inscrit à un cours d\'école d\'été pour cette année.')
    return SummerSchoolEnrollOut(
        id=enroll.id,
        student_fiche=student.fiche,
        student_name=student.full_name,
        course_code=course.local_code,
        course_desc=course.description,
        academic_year=enroll.academic_year,
        enrolled_at=enroll.enrolled_at.isoformat(),
    )


@router.delete("/summer-school/{enrollment_id}")
def summer_school_cancel(request, enrollment_id: int):
    enroll = get_object_or_404(SummerSchoolEnrollment, id=enrollment_id)
    enroll.delete()
    return {'ok': True}


@router.get("/summer-school/{year}/{course_code}", response=List[SummerSchoolEnrollOut])
def summer_school_list(request, year: str, course_code: str):
    enrollments = (
        SummerSchoolEnrollment.objects
        .filter(academic_year=year, course__local_code=course_code)
        .select_related('student', 'course')
        .order_by('student__full_name')
    )
    return [
        SummerSchoolEnrollOut(
            id=e.id,
            student_fiche=e.student.fiche,
            student_name=e.student.full_name,
            course_code=e.course.local_code,
            course_desc=e.course.description,
            academic_year=e.academic_year,
            enrolled_at=e.enrolled_at.isoformat(),
        )
        for e in enrollments
    ]


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
    return get_object_or_404(
        Student.objects.prefetch_related(
            'results__offering__course',
            'results__offering__teacher',
        ),
        fiche=fiche,
    )


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
