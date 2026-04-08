from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Any, Optional

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
            return int(float(v))
        except (ValueError, TypeError):
            raise ValueError("Le numéro de fiche doit être un nombre entier.")

    @field_validator("code_permanent")
    @classmethod
    def validate_code_permanent(cls, v: str):
        if not v:
            raise ValueError("Le code permanent est obligatoire.")
        if len(v) < 12:
            v = v.ljust(12, 'X')
        elif len(v) > 12:
            raise ValueError(f"Le code permanent est trop long (actuel: {len(v)})")
        return v.upper()

    @field_validator("statut")
    @classmethod
    def validate_statut(cls, v: str):
        if v not in ["Actif", "Inactif"]:
            raise ValueError(f"Statut inconnu: '{v}'. Attendu: 'Actif' ou 'Inactif'")
        return v

class ResultatRowSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    fiche: int = Field(..., alias="Fiche")
    course_code: str = Field(..., alias="Matière")
    course_description: str = Field(..., alias="Description de la matière")
    course_group: str = Field(..., alias="Grp")
    teacher_name: Optional[str] = Field(None, alias="Nom et prénom de l'enseignant")
    step_1_grade: Optional[int] = Field(None, alias="[1]")
    step_2_grade: Optional[int] = Field(None, alias="[2]")
    final_grade: Optional[int] = Field(None, alias="Som. Final")

    @field_validator("course_code", "course_description", "course_group", "teacher_name", mode="before")
    @classmethod
    def cast_to_str(cls, v: Any):
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("step_1_grade", "step_2_grade", "final_grade", mode="before")
    @classmethod
    def validate_grade(cls, v: Any):
        # On retourne None pour les valeurs vides, NaN ou textuelles (ex: "ABS")
        if v is None or v == "" or str(v).strip().upper() in ["ABS", "NAN", "NaN"]:
            return None
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return None
