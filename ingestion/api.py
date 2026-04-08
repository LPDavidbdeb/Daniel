import pandas as pd
from typing import List, Dict, Any, Tuple
from ninja import Router, File, UploadedFile
from ninja.errors import HttpError
from pydantic import ValidationError
from django.db import transaction
from .schemas import EleveRowSchema, ResultatRowSchema
from students.models import Student, AcademicResult

router = Router()

def get_cleaned_dataframe(file: UploadedFile, required_columns: List[str]) -> pd.DataFrame:
    """Helper pour lire et nettoyer le fichier GPI."""
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, engine='openpyxl' if file.name.endswith('.xlsx') else None)
        else:
            raise HttpError(400, "Format de fichier non supporté. Utilisez .csv ou .xlsx.")
    except Exception as e:
        raise HttpError(400, f"Erreur lors de la lecture du fichier : {str(e)}")

    df.columns = [col.strip() for col in df.columns]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise HttpError(400, f"Colonnes manquantes : {', '.join(missing_columns)}.")

    return df.where(pd.notnull(df), None)

@router.post("/preview-eleves")
def preview_eleves(request, file: UploadedFile = File(...)):
    required = ["Fiche", "Code permanent", "Nom et prénom", "Statut", "Classe", "Groupe-repère"]
    df = get_cleaned_dataframe(file, required)
    
    total_lignes = len(df)
    lignes_valides = 0
    erreurs = []

    for index, row in df.iterrows():
        row_dict = row.to_dict()
        try:
            EleveRowSchema(**row_dict)
            lignes_valides += 1
        except ValidationError as e:
            error_details = [f"[{err['loc'][-1]}] {err['msg'].replace('Value error, ', '')}" for err in e.errors()]
            erreurs.append({
                "ligne": int(index) + 2,
                "identifiant": str(row_dict.get("Nom et prénom") or f"Fiche {row_dict.get('Fiche', '???')}"),
                "messages": error_details
            })

    return {"total_lignes": total_lignes, "lignes_valides": lignes_valides, "erreurs": erreurs}

@router.post("/commit-eleves")
def commit_eleves(request, file: UploadedFile = File(...)):
    required = ["Fiche", "Code permanent", "Nom et prénom", "Statut", "Classe", "Groupe-repère"]
    df = get_cleaned_dataframe(file, required)
    
    valid_rows = []
    fiches_entrantes = set()

    for _, row in df.iterrows():
        try:
            val_row = EleveRowSchema(**row.to_dict())
            valid_rows.append(val_row)
            fiches_entrantes.add(val_row.fiche)
        except ValidationError:
            continue

    with transaction.atomic():
        for row in valid_rows:
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
        Student.objects.filter(is_active=True).exclude(fiche__in=fiches_entrantes).update(is_active=False)

    return {"success": True, "summary": {"processed": len(valid_rows)}}

# --- INGESTION RÉSULTATS ---

@router.post("/preview-results")
def preview_results(request, file: UploadedFile = File(...)):
    required = ["Fiche", "Matière", "Grp", "[1]", "[2]", "Som. Final", "Description de la matière", "Nom et prénom de l'enseignant"]
    df = get_cleaned_dataframe(file, required)
    
    # Cache des fiches existantes
    existing_fiches = set(Student.objects.values_list('fiche', flat=True))
    
    total_lignes = len(df)
    lignes_valides = 0
    erreurs = []

    for index, row in df.iterrows():
        row_dict = row.to_dict()
        fiche = row_dict.get("Fiche")
        
        # 1. Vérification intégrité référentielle
        if fiche not in existing_fiches:
            erreurs.append({
                "ligne": int(index) + 2,
                "identifiant": f"Fiche {fiche}",
                "messages": ["Élève introuvable dans la base de données. Veuillez d'abord mettre à jour la liste des élèves."]
            })
            continue

        # 2. Validation Pydantic
        try:
            ResultatRowSchema(**row_dict)
            lignes_valides += 1
        except ValidationError as e:
            error_details = [f"[{err['loc'][-1]}] {err['msg'].replace('Value error, ', '')}" for err in e.errors()]
            erreurs.append({
                "ligne": int(index) + 2,
                "identifiant": f"Fiche {fiche} - {row_dict.get('Matière')}",
                "messages": error_details
            })

    return {"total_lignes": total_lignes, "lignes_valides": lignes_valides, "erreurs": erreurs}

@router.post("/commit-results")
def commit_results(request, file: UploadedFile = File(...)):
    required = ["Fiche", "Matière", "Grp", "[1]", "[2]", "Som. Final", "Description de la matière", "Nom et prénom de l'enseignant"]
    df = get_cleaned_dataframe(file, required)
    
    # Cache des fiches existantes (on ignore silencieusement les lignes sans étudiant valide au commit)
    existing_fiches = set(Student.objects.values_list('fiche', flat=True))
    
    valid_rows = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        if row_dict.get("Fiche") in existing_fiches:
            try:
                valid_rows.append(ResultatRowSchema(**row_dict))
            except ValidationError:
                continue

    with transaction.atomic():
        for row in valid_rows:
            AcademicResult.objects.update_or_create(
                student_id=row.fiche,
                course_code=row.course_code,
                defaults={
                    "course_description": row.course_description,
                    "course_group": row.course_group,
                    "teacher_name": row.teacher_name,
                    "step_1_grade": row.step_1_grade,
                    "step_2_grade": row.step_2_grade,
                    "final_grade": row.final_grade,
                }
            )

    return {"success": True, "count": len(valid_rows)}
