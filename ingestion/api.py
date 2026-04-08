import pandas as pd
from typing import List, Dict, Any
from ninja import Router, File, UploadedFile
from ninja.errors import HttpError
from pydantic import ValidationError
from .schemas import EleveRowSchema

router = Router()

@router.post("/preview-eleves")
def preview_eleves(request, file: UploadedFile = File(...)):
    # 1. Lecture du fichier
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, engine='openpyxl' if file.name.endswith('.xlsx') else None)
        else:
            raise HttpError(400, "Format de fichier non supporté. Utilisez .csv ou .xlsx.")
    except Exception as e:
        raise HttpError(400, f"Erreur lors de la lecture du fichier : {str(e)}")

    # 2. Validation des colonnes obligatoires (Alias strict de GPI)
    required_columns = [
        "Fiche", "Code permanent", "Nom et prénom", 
        "Statut", "Classe", "Groupe-repère"
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise HttpError(400, f"Colonnes manquantes : {', '.join(missing_columns)}. Veuillez vérifier votre extraction GPI.")

    # 3. Validation ligne par ligne
    total_lignes = len(df)
    lignes_valides = 0
    erreurs = []

    # On remplace les NaN par None pour que Pydantic puisse valider les champs optionnels ou lever des erreurs explicites
    df = df.where(pd.notnull(df), None)
    
    for index, row in df.iterrows():
        row_dict = row.to_dict()
        try:
            # On tente de valider la ligne
            EleveRowSchema(**row_dict)
            lignes_valides += 1
        except ValidationError as e:
            # On compile les erreurs Pydantic
            error_details = []
            for err in e.errors():
                # On nettoie le message Pydantic pour garder notre message personnalisé
                msg = err['msg'].replace("Value error, ", "")
                error_details.append(msg)
            
            erreurs.append({
                "ligne": int(index) + 2,  # +2 car index 0 et header
                "identifiant": str(row_dict.get("Nom et prénom", f"Fiche {row_dict.get('Fiche', 'Inconnue')}")),
                "messages": error_details
            })

    return {
        "total_lignes": total_lignes,
        "lignes_valides": lignes_valides,
        "erreurs": erreurs
    }
