from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Any

class EleveRowSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    fiche: int = Field(..., alias="Fiche")
    code_permanent: str = Field(..., alias="Code permanent")
    nom_prenom: str = Field(..., alias="Nom et prénom")
    statut: str = Field(..., alias="Statut")
    classe: str = Field(..., alias="Classe")
    groupe_repere: str = Field(..., alias="Groupe-repère")

    @field_validator("code_permanent", "nom_prenom", "statut", "classe", "groupe_repere", mode="before")
    @classmethod
    def cast_to_str(cls, v: Any):
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("fiche", mode="before")
    @classmethod
    def validate_fiche(cls, v):
        try:
            return int(float(v)) # Gère le cas où Excel lit "123.0"
        except (ValueError, TypeError):
            raise ValueError("Le numéro de fiche doit être un nombre entier.")

    @field_validator("code_permanent")
    @classmethod
    def validate_code_permanent(cls, v: str):
        if not v or len(v) != 12:
            raise ValueError(f"Le code permanent doit avoir 12 caractères (actuel: {len(v)})")
        return v.upper()

    @field_validator("statut")
    @classmethod
    def validate_statut(cls, v: str):
        if v not in ["Actif", "Inactif"]:
            raise ValueError(f"Statut inconnu: '{v}'. Attendu: 'Actif' ou 'Inactif'")
        return v
