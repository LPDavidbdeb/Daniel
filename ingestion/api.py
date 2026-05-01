import pandas as pd
import unicodedata
import re
from typing import List, Dict, Any, Tuple, Set
from ninja import Router, File, UploadedFile, Form
from ninja.errors import HttpError
from pydantic import ValidationError
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import ImportLog
from .schemas import EleveRowSchema, ResultatRowSchema
from students.models import Student, AcademicResult
from school.models import Course, Teacher, CourseOffering

from ninja_jwt.authentication import JWTAuth

User = get_user_model()
router = Router(auth=JWTAuth())

def _require_superuser(request) -> None:
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or not user.is_superuser:
        raise HttpError(403, "Accès refusé : Droits d'administrateur requis.")

def slugify_name(name):
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[^\w\s-]', '', name).strip().lower()
    return re.sub(r'[-\s]+', '.', name)

def get_cleaned_dataframe(file: UploadedFile, required_columns: List[str]) -> pd.DataFrame:
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, engine='openpyxl' if file.name.endswith('.xlsx') else None)
        else:
            raise HttpError(400, "Format non supporté.")
    except Exception as e:
        raise HttpError(400, f"Erreur lecture : {str(e)}")

    df.columns = [col.strip() for col in df.columns]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise HttpError(400, f"Colonnes manquantes : {', '.join(missing)}")
    return df.where(pd.notnull(df), None)

@router.post("/preview-eleves")
def preview_eleves(request, file: UploadedFile = File(...)):
    _require_superuser(request)
    required = ["Fiche", "Code permanent", "Nom et prénom", "Statut", "Classe", "Groupe-repère"]
    df = get_cleaned_dataframe(file, required)
    total, valides, erreurs = len(df), 0, []
    for index, row in df.iterrows():
        try:
            EleveRowSchema(**row.to_dict())
            valides += 1
        except ValidationError as e:
            erreurs.append({
                "ligne": int(index) + 2,
                "identifiant": str(row.get("Nom et prénom") or f"Fiche {row.get('Fiche')}"),
                "messages": [f"[{err['loc'][-1]}] {err['msg']}" for err in e.errors()]
            })
    return {"total_lignes": total, "lignes_valides": valides, "erreurs": erreurs}

@router.post("/commit-eleves")
def commit_eleves(request, file: UploadedFile = File(...), dry_run: bool = Form(False)):
    _require_superuser(request)
    required = ["Fiche", "Code permanent", "Nom et prénom", "Statut", "Classe", "Groupe-repère"]
    df = get_cleaned_dataframe(file, required)
    valid_rows, fiches_entrantes = [], set()
    for _, row in df.iterrows():
        try:
            val_row = EleveRowSchema(**row.to_dict())
            valid_rows.append(val_row)
            fiches_entrantes.add(val_row.fiche)
        except ValidationError: continue

    stats = {"created": 0, "updated": 0, "deactivated": 0}
    
    with transaction.atomic():
        # Identify who would be deactivated
        to_deactivate_qs = Student.objects.filter(is_active=True).exclude(fiche__in=fiches_entrantes)
        stats["deactivated"] = to_deactivate_qs.count()

        for row in valid_rows:
            student = Student.objects.filter(fiche=row.fiche).first()
            if not student:
                stats["created"] += 1
            else:
                stats["updated"] += 1
            
            if not dry_run:
                Student.objects.update_or_create(
                    fiche=row.fiche,
                    defaults={
                        "permanent_code": row.code_permanent, 
                        "full_name": row.nom_prenom, 
                        "level": row.classe, 
                        "current_group": row.groupe_repere, 
                        "is_active": True
                    }
                )
        
        if not dry_run:
            to_deactivate_qs.update(is_active=False)
            
    # Audit Logging
    ImportLog.objects.create(
        user=request.user,
        import_type='ELEVES',
        filename=file.name,
        dry_run=dry_run,
        stats=stats
    )
            
    return {"success": True, "dry_run": dry_run, "stats": stats}

@router.post("/preview-results")
def preview_results(request, file: UploadedFile = File(...)):
    _require_superuser(request)
    required = ["Fiche", "Matière", "Grp", "[1]", "[2]", "Som. Final", "Description de la matière", "Nom et prénom de l'enseignant"]
    df = get_cleaned_dataframe(file, required)
    existing_fiches = set(Student.objects.values_list('fiche', flat=True))
    total, valides, erreurs = len(df), 0, []
    for index, row in df.iterrows():
        row_dict = row.to_dict()
        if row_dict.get("Fiche") not in existing_fiches:
            erreurs.append({"ligne": int(index)+2, "identifiant": f"Fiche {row_dict.get('Fiche')}", "messages": ["Élève introuvable. Importez les élèves d'abord."]})
            continue
        try:
            ResultatRowSchema(**row_dict)
            valides += 1
        except ValidationError as e:
            erreurs.append({
                "ligne": int(index)+2, "identifiant": f"Fiche {row_dict.get('Fiche')}",
                "messages": [f"[{err['loc'][-1]}] {err['msg']}" for err in e.errors()]
            })
    return {"total_lignes": total, "lignes_valides": valides, "erreurs": erreurs}

@router.post("/commit-results")
def commit_results(request, file: UploadedFile = File(...), academic_year: str = Form(...), dry_run: bool = Form(False)):
    _require_superuser(request)
    required = ["Fiche", "Matière", "Grp", "[1]", "[2]", "Som. Final", "Description de la matière", "Nom et prénom de l'enseignant"]
    df = get_cleaned_dataframe(file, required)
    teacher_group, _ = Group.objects.get_or_create(name='Professeurs')
    existing_fiches = set(Student.objects.values_list('fiche', flat=True))

    offres_entrantes: Set[Tuple[str, str, str]] = set() # (LocalCode, Grp, Year)
    import_errors = []
    stats = {"results_updated": 0, "offerings_created": 0, "offerings_deactivated": 0}

    with transaction.atomic():
        for index, row in df.iterrows():
            row_dict = row.to_dict()
            if row_dict.get("Fiche") not in existing_fiches: continue
            
            try:
                val = ResultatRowSchema(**row_dict)
                course_matches = Course.objects.filter(meq_code=val.course_code)
                if not course_matches.exists():
                    import_errors.append(f"Ligne {index+2} : Code MEQ {val.course_code} introuvable.")
                    continue
                
                course = None
                if course_matches.count() > 1:
                    course = course_matches.filter(stream='ZENITH').first() if 'Z' in val.course_group.upper() else course_matches.exclude(stream='ZENITH').first()
                    course = course or course_matches.first()
                else:
                    course = course_matches.first()

                teacher = None
                if val.teacher_name:
                    teacher = Teacher.objects.filter(full_name=val.teacher_name).first()
                    if not teacher:
                        parts = val.teacher_name.split(' ', 1)
                        first, last = parts[0], parts[1] if len(parts)>1 else ""
                        email = f"{slugify_name(first)}.{slugify_name(last)}@csspi.qc.ca"
                        user, created = User.objects.get_or_create(email=email, defaults={'first_name': first, 'last_name': last, 'is_active': True})
                        if created and not dry_run:
                            user.set_unusable_password()
                            user.groups.add(teacher_group)
                            user.save()
                        if not dry_run:
                            teacher = Teacher.objects.create(user=user, full_name=val.teacher_name)
                    elif not dry_run:
                        teacher.is_active = True
                        teacher.save()

                offering_exists = CourseOffering.objects.filter(course=course, group_number=val.course_group, academic_year=academic_year).exists()
                if not offering_exists:
                    stats["offerings_created"] += 1

                if not dry_run:
                    offering, _ = CourseOffering.objects.update_or_create(
                        course=course, group_number=val.course_group, academic_year=academic_year,
                        defaults={'teacher': teacher, 'is_active': True}
                    )
                    AcademicResult.objects.update_or_create(
                        student_id=val.fiche, offering=offering,
                        defaults={'academic_year': academic_year, 'step_1_grade': val.step_1_grade, 'step_2_grade': val.step_2_grade, 'final_grade': val.final_grade}
                    )
                
                offres_entrantes.add((course.local_code, val.course_group, academic_year))
                stats["results_updated"] += 1
            except ValidationError: continue

        to_deactivate_qs = CourseOffering.objects.filter(is_active=True, academic_year=academic_year)
        for off in to_deactivate_qs:
            if (off.course.local_code, off.group_number, academic_year) not in offres_entrantes:
                stats["offerings_deactivated"] += 1
                if not dry_run:
                    off.is_active = False
                    off.save()

    # Audit Logging
    ImportLog.objects.create(
        user=request.user,
        import_type='RESULTATS',
        filename=file.name,
        academic_year=academic_year,
        dry_run=dry_run,
        stats=stats,
        errors=import_errors
    )

    return {"success": True, "dry_run": dry_run, "stats": stats, "errors": import_errors}
