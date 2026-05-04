from django.db import models


class CourseEvalState(models.TextChoices):
    """Micro-level evaluation state for a single course result."""
    PASS = "PASS", "Réussite (≥60)"
    TEACHER_REVIEW_PENDING = "TEACHER_REVIEW_PENDING", "Avis enseignant requis (57-59)"
    SUMMER_ELIGIBLE = "SUMMER_ELIGIBLE", "Admissible aux cours d'été (50-56, cours de base)"
    FAILED = "FAILED", "Échec (< 50 ou 50-56 cours non-sanctionné)"


class CourseState(models.TextChoices):
    PASS = "PASS", "Réussite"
    FAIL_NON_SUMMER = "FAIL_NON_SUMMER", "Échec (non admissible aux cours d'été)"
    SUMMER_ELIGIBLE = "SUMMER_ELIGIBLE", "Admissible aux cours d'été"
    SUMMER_ELIGIBLE_TEACHER_REVIEW = "SUMMER_ELIGIBLE_TEACHER_REVIEW", "Admissible aux cours d'été (avis de l'enseignant requis)"


class WorkflowState(models.TextChoices):
    IFP_CANDIDATE_REVIEW = "IFP_CANDIDATE_REVIEW", "Révision des candidats IFP"
    REGULAR_REVIEW_PENDING = "REGULAR_REVIEW_PENDING", "Révision régulière en attente"
    READY_FOR_FINALIZATION = "READY_FOR_FINALIZATION", "Prêt pour finalisation"

class FinalAprilState(models.TextChoices):
    APRIL_FINAL_PROMOTE_REGULAR = "APRIL_FINAL_PROMOTE_REGULAR", "Promotion régulière"
    APRIL_FINAL_PROMOTE_WITH_SUMMER = "APRIL_FINAL_PROMOTE_WITH_SUMMER", "Promotion avec cours d'été"
    APRIL_FINAL_HOLDBACK = "APRIL_FINAL_HOLDBACK", "Doublement"
    APRIL_FINAL_IFP_N = "APRIL_FINAL_IFP_N", "IFP N"
    APRIL_FINAL_IFP_N_MINUS_1 = "APRIL_FINAL_IFP_N_MINUS_1", "IFP N-1"

class VettingStatus(models.TextChoices):
    AUTO_VETTED = "AUTO_VETTED", "Validé automatiquement"
    REQUIRES_REVIEW = "REQUIRES_REVIEW", "Nécessite une révision"
    MANUALLY_VETTED = "MANUALLY_VETTED", "Validé manuellement"
