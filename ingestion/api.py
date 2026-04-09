import pandas as pd
import unicodedata
import re
from typing import List, Dict, Any, Tuple, Set
from ninja import Router, File, UploadedFile
from ninja.errors import HttpError
from pydantic import ValidationError
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .schemas import EleveRowSchema, ResultatRowSchema
from students.models import Student, AcademicResult
from school.models import Course, Teacher, CourseOffering

User = get_user_model()
router = Router()

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
def commit_eleves(request, file: UploadedFile = File(...)):
    required = ["Fiche", "Code permanent", "Nom et prénom", "Statut", "Classe", "Groupe-repère"]
    df = get_cleaned_dataframe(file, required)
    valid_rows, fiches_entrantes = [], set()
    for _, row in df.iterrows():
        try:
            val_row = EleveRowSchema(**row.to_dict())
            valid_rows.append(val_row)
            fiches_entrantes.add(val_row.fiche)
        except ValidationError: continue

    with transaction.atomic():
        for row in valid_rows:
            Student.objects.update_or_create(
                fiche=row.fiche,
                defaults={"permanent_code": row.code_permanent, "full_name": row.nom_prenom, "level": row.classe, "current_group": row.groupe_repere, "is_active": True}
            )
        Student.objects.filter(is_active=True).exclude(fiche__in=fiches_entrantes).update(is_active=False)
    return {"success": True, "count": len(valid_rows)}

@router.post("/preview-results")
def preview_results(request, file: UploadedFile = File(...)):
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
def commit_results(request, file: UploadedFile = File(...)):
    required = ["Fiche", "Matière", "Grp", "[1]", "[2]", "Som. Final", "Description de la matière", "Nom et prénom de l'enseignant"]
    df = get_cleaned_dataframe(file, required)
    teacher_group, _ = Group.objects.get_or_create(name='Professeurs')
    existing_fiches = set(Student.objects.values_list('fiche', flat=True))

    # Sets pour le tracking (Diff logic)
    codes_cours_entrants: Set[str] = set()
    noms_profs_entrants: Set[str] = set()
    offres_entrantes: Set[Tuple[str, str]] = set() # (CodeCours, Grp)

    with transaction.atomic():
        count = 0
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            if row_dict.get("Fiche") not in existing_fiches: continue
            try:
                val = ResultatRowSchema(**row_dict)
                
                # 1. Course Sync
                course, _ = Course.objects.update_or_create(
                    code=val.course_code, 
                    defaults={'description': val.course_description, 'is_active': True}
                )
                codes_cours_entrants.add(course.code)
                
                # 2. Teacher & User Sync
                teacher = None
                if val.teacher_name:
                    noms_profs_entrants.add(val.teacher_name)
                    teacher = Teacher.objects.filter(full_name=val.teacher_name).first()
                    if not teacher:
                        parts = val.teacher_name.split(' ', 1)
                        first, last = parts[0], parts[1] if len(parts)>1 else ""
                        email = f"{slugify_name(first)}.{slugify_name(last)}@csspi.qc.ca"
                        user, _ = User.objects.update_or_create(
                            email=email, 
                            defaults={'first_name': first, 'last_name': last, 'is_active': True}
                        )
                        user.set_unusable_password()
                        user.groups.add(teacher_group)
                        user.save()
                        teacher = Teacher.objects.create(user=user, full_name=val.teacher_name)
                    else:
                        # Réactiver le prof et son utilisateur s'ils étaient inactifs
                        teacher.is_active = True
                        teacher.save()
                        if teacher.user:
                            teacher.user.is_active = True
                            teacher.user.save()

                # 3. Course Offering Sync
                offering, _ = CourseOffering.objects.update_or_create(
                    course=course, 
                    group_number=val.course_group, 
                    defaults={'teacher': teacher, 'is_active': True}
                )
                offres_entrantes.add((course.code, offering.group_number))

                # 4. Result Update
                AcademicResult.objects.update_or_create(
                    student_id=val.fiche, offering=offering,
                    defaults={'step_1_grade': val.step_1_grade, 'step_2_grade': val.step_2_grade, 'final_grade': val.final_grade}
                )
                count += 1
            except ValidationError: continue

        # --- LOGIQUE DE DIFF (SOFT DELETE) ---
        # On désactive ce qui n'est plus dans le fichier résultats actuel
        
        # Désactiver les offres de cours disparues
        offerings_to_deactivate = CourseOffering.objects.filter(is_active=True)
        for off in offerings_to_deactivate:
            if (off.course.code, off.group_number) not in offres_entrantes:
                off.is_active = False
                off.save()

        # Désactiver les professeurs disparus (Attention: seulement ceux qui n'ont plus aucune offre active)
        profs_to_deactivate = Teacher.objects.filter(is_active=True).exclude(full_name__in=noms_profs_entrants)
        for prof in profs_to_deactivate:
            prof.is_active = False
            prof.save()
            if prof.user:
                prof.user.is_active = False
                prof.user.save()

    return {"success": True, "count": count}
