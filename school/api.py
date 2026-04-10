from typing import List
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth
from .models import Course, CourseOffering, Teacher, MeqReference
from .schemas import (
    CourseCrudIn,
    CourseCrudOut,
    CourseOfferingCrudIn,
    CourseOfferingCrudOut,
    TeacherCrudIn,
    TeacherCrudOut,
    TeacherDetailOut,
)

router = Router(auth=JWTAuth())
INVALID_MEQ_CODE_MESSAGE = "Le code MEQ fourni n'existe pas dans le référentiel officiel du Ministère."


def _require_superuser(request) -> None:
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or not user.is_superuser:
        raise HttpError(403, 'Acces refuse: superuser requis.')


def _normalize_meq_code(meq_code: str | None) -> str | None:
    if meq_code is None:
        return None
    normalized = meq_code.strip()
    return normalized or None


def _validate_meq_code(meq_code: str | None) -> str | None:
    normalized = _normalize_meq_code(meq_code)
    if not normalized:
        return None
    if not MeqReference.objects.filter(meq_code=normalized).exists():
        raise HttpError(422, INVALID_MEQ_CODE_MESSAGE)
    return normalized


@router.get('/teachers', response=List[TeacherDetailOut])
def list_teachers(request):
    teachers = Teacher.objects.filter(is_active=True).prefetch_related('offerings__course', 'user')

    results = []
    for teacher in teachers:
        offerings_data = []
        for offering in teacher.offerings.all():
            offerings_data.append({
                'id': offering.id,
                "course_local_code": offering.course.local_code,
                "course_description": offering.course.description,
                'group_number': offering.group_number,
                'results': [],
            })

        results.append({
            'id': teacher.id,
            'full_name': teacher.full_name,
            'email': teacher.user.email if teacher.user else 'N/A',
            'offerings': offerings_data,
        })
    return results


@router.get('/{teacher_id}', response=TeacherDetailOut)
def get_teacher_detail(request, teacher_id: int):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    offerings_data = []
    for offering in teacher.offerings.all().prefetch_related('results__student', 'course'):
        offerings_data.append({
            'id': offering.id,
            "course_local_code": offering.course.local_code,
            "course_description": offering.course.description,
            'group_number': offering.group_number,
            'results': [
                {
                    'student': {'fiche': r.student.fiche, 'full_name': r.student.full_name},
                    'step_1_grade': r.step_1_grade,
                    'step_2_grade': r.step_2_grade,
                    'final_grade': r.final_grade,
                }
                for r in offering.results.all()
            ],
        })
    return {
        'id': teacher.id,
        'full_name': teacher.full_name,
        'email': teacher.user.email if teacher.user else 'N/A',
        'offerings': offerings_data,
    }


@router.get('/crud/courses', response=List[CourseCrudOut])
def list_courses_crud(request):
    _require_superuser(request)
    return Course.objects.all().order_by('local_code')


@router.post('/crud/courses', response=CourseCrudOut)
def create_course_crud(request, payload: CourseCrudIn):
    _require_superuser(request)
    valid_meq_code = _validate_meq_code(payload.meq_code)
    try:
        return Course.objects.create(
            local_code=payload.local_code,
            meq_code=valid_meq_code,
            description=payload.description,
            level=payload.level,
            credits=payload.credits,
            periods=payload.periods,
            is_core_or_sanctioned=payload.is_core_or_sanctioned,
            is_active=payload.is_active,
        )
    except IntegrityError:
        raise HttpError(409, 'Conflit: code local deja utilise.')


@router.put('/crud/courses/{course_id}', response=CourseCrudOut)
def update_course_crud(request, course_id: int, payload: CourseCrudIn):
    _require_superuser(request)
    course = get_object_or_404(Course, id=course_id)
    valid_meq_code = _validate_meq_code(payload.meq_code)
    course.local_code = payload.local_code
    course.meq_code = valid_meq_code
    course.description = payload.description
    course.level = payload.level
    course.credits = payload.credits
    course.periods = payload.periods
    course.is_core_or_sanctioned = payload.is_core_or_sanctioned
    course.is_active = payload.is_active
    try:
        course.save()
    except IntegrityError:
        raise HttpError(409, 'Conflit: code local deja utilise.')
    return course


@router.delete('/crud/courses/{course_id}')
def delete_course_crud(request, course_id: int):
    _require_superuser(request)
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    return {'ok': True}


@router.get('/crud/teachers', response=List[TeacherCrudOut])
def list_teachers_crud(request):
    _require_superuser(request)
    return Teacher.objects.select_related('user').all().order_by('full_name')


@router.post('/crud/teachers', response=TeacherCrudOut)
def create_teacher_crud(request, payload: TeacherCrudIn):
    _require_superuser(request)
    user = get_object_or_404(get_user_model(), id=payload.user)
    try:
        return Teacher.objects.create(
            user=user,
            full_name=payload.full_name,
            is_active=payload.is_active,
        )
    except IntegrityError:
        raise HttpError(409, 'Conflit: enseignant ou utilisateur deja associe.')


@router.put('/crud/teachers/{teacher_id}', response=TeacherCrudOut)
def update_teacher_crud(request, teacher_id: int, payload: TeacherCrudIn):
    _require_superuser(request)
    teacher = get_object_or_404(Teacher, id=teacher_id)
    user = get_object_or_404(get_user_model(), id=payload.user)
    teacher.user = user
    teacher.full_name = payload.full_name
    teacher.is_active = payload.is_active
    try:
        teacher.save()
    except IntegrityError:
        raise HttpError(409, 'Conflit: enseignant ou utilisateur deja associe.')
    return teacher


@router.delete('/crud/teachers/{teacher_id}')
def delete_teacher_crud(request, teacher_id: int):
    _require_superuser(request)
    teacher = get_object_or_404(Teacher, id=teacher_id)
    teacher.delete()
    return {'ok': True}


@router.get('/crud/course-offerings', response=List[CourseOfferingCrudOut])
def list_course_offerings_crud(request):
    _require_superuser(request)
    return CourseOffering.objects.all().order_by('academic_year', 'group_number')


@router.post('/crud/course-offerings', response=CourseOfferingCrudOut)
def create_course_offering_crud(request, payload: CourseOfferingCrudIn):
    _require_superuser(request)
    course = get_object_or_404(Course, id=payload.course)
    teacher = get_object_or_404(Teacher, id=payload.teacher) if payload.teacher else None
    try:
        return CourseOffering.objects.create(
            course=course,
            group_number=payload.group_number,
            academic_year=payload.academic_year,
            teacher=teacher,
            is_active=payload.is_active,
        )
    except IntegrityError:
        raise HttpError(409, 'Conflit: groupe deja existant pour cette annee.')


@router.put('/crud/course-offerings/{offering_id}', response=CourseOfferingCrudOut)
def update_course_offering_crud(request, offering_id: int, payload: CourseOfferingCrudIn):
    _require_superuser(request)
    offering = get_object_or_404(CourseOffering, id=offering_id)
    offering.course = get_object_or_404(Course, id=payload.course)
    offering.teacher = get_object_or_404(Teacher, id=payload.teacher) if payload.teacher else None
    offering.group_number = payload.group_number
    offering.academic_year = payload.academic_year
    offering.is_active = payload.is_active
    try:
        offering.save()
    except IntegrityError:
        raise HttpError(409, 'Conflit: groupe deja existant pour cette annee.')
    return offering


@router.delete('/crud/course-offerings/{offering_id}')
def delete_course_offering_crud(request, offering_id: int):
    _require_superuser(request)
    offering = get_object_or_404(CourseOffering, id=offering_id)
    offering.delete()
    return {'ok': True}
