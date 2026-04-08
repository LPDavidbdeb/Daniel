import pandas as pd
from typing import List, Dict, Any, Tuple
from ninja import Router, File, UploadedFile
from ninja.errors import HttpError
from pydantic import ValidationError
from django.db import transaction
from .schemas import EleveRowSchema
from students.models import Student

router = Router()

def get_cleaned_dataframe(file: UploadedFile) -> pd.DataFrame:
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

    # Nettoyage des noms de colonnes
    df.columns = [col.strip() for col in df.columns]

    # Validation des colonnes minimales
    required_columns = ["Fiche", "Code permanent", "Nom et prénom", "Statut", "Classe", "Groupe-repère"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise HttpError(400, f"Colonnes manquantes : {', '.join(missing_columns)}.")

    # Remplacement des NaN par None
    return df.where(pd.notnull(df), None)

@router.post("/preview-eleves")
def preview_eleves(request, file: UploadedFile = File(...)):
    df = get_cleaned_dataframe(file)
    
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

    return {
        "total_lignes": total_lignes,
        "lignes_valides": lignes_valides,
        "erreurs": erreurs
    }

@router.post("/commit-eleves")
def commit_eleves(request, file: UploadedFile = File(...)):
    """Exécution finale de l'importation avec logique de synchronisation (Diff)."""
    df = get_cleaned_dataframe(file)
    
    created_count = 0
    updated_count = 0
    deactivated_count = 0
    
    # On ne traite que les lignes 100% valides selon le schéma Pydantic
    valid_rows = []
    fiches_entrantes = set()

    for _, row in df.iterrows():
        row_dict = row.to_dict()
        try:
            validated_row = EleveRowSchema(**row_dict)
            valid_rows.append(validated_row)
            fiches_entrantes.add(validated_row.fiche)
        except ValidationError:
            continue # On ignore les lignes invalides lors du commit final (déjà filtrées par le preview)

    with transaction.atomic():
        # 1. Mise à jour ou Création (Upsert)
        for row in valid_rows:
            student, created = Student.objects.update_or_create(
                fiche=row.fiche,
                defaults={
                    "permanent_code": row.code_permanent,
                    "full_name": row.nom_prenom,
                    "level": row.classe,
                    "current_group": row.groupe_repere,
                    "is_active": True # On réactive l'élève s'il était inactif
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        # 2. Logique de Diff (Soft-Delete)
        # On trouve les élèves actifs en BD qui ne sont PAS dans le fichier
        to_deactivate = Student.objects.filter(is_active=True).exclude(fiche__in=fiches_entrantes)
        deactivated_count = to_deactivate.count()
        to_deactivate.update(is_active=False)

    return {
        "success": True,
        "summary": {
            "created": created_count,
            "updated": updated_count,
            "deactivated": deactivated_count,
            "total_processed": len(valid_rows)
        }
    }
