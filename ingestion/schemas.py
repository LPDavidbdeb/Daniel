from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal

class EleveRowSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    fiche: int = Field(..., alias="Fiche")
    code_permanent: str = Field(..., alias="Code permanent")
    nom_prenom: str = Field(..., alias="Nom et prénom")
    statut: Literal["Actif", "Inactif"] = Field(..., alias="Statut")
    classe: str = Field(..., alias="Classe")
    groupe_repere: str = Field(..., alias="Groupe-repère")

    @field_validator("fiche", mode="before")
    @classmethod
    def validate_fiche(cls, v):
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError("Le numéro de fiche doit être un nombre entier valide.")

    @field_validator("code_permanent")
    @classmethod
    def validate_code_permanent(cls, v):
        if not v or len(str(v).strip()) != 12:
            raise ValueError("Le code permanent doit contenir exactement 12 caractères.")
        return str(v).strip().upper()

    @field_validator("statut")
    @classmethod
    def validate_statut(cls, v):
        if v not in ["Actif", "Inactif"]:
            raise ValueError("Le statut doit être 'Actif' ou 'Inactif'.")
        return v
