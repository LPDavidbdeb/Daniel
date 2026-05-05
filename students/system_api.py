from ninja import Router

from students.constants import (
    FAIL_HARD_BLOCK_THRESHOLD,
    MAX_SUMMER_CLASSES,
    PASS_THRESHOLD,
    SUMMER_ELIGIBLE_MAX,
    SUMMER_ELIGIBLE_MIN,
    TEACHER_REVIEW_MAX,
    TEACHER_REVIEW_MIN,
)

router = Router(tags=["system"])


@router.get("/rules-audit", auth=None)
def rules_audit(request):
    return {
        "constants": {
            "PASS_THRESHOLD": PASS_THRESHOLD,
            "TEACHER_REVIEW_MIN": TEACHER_REVIEW_MIN,
            "TEACHER_REVIEW_MAX": TEACHER_REVIEW_MAX,
            "SUMMER_ELIGIBLE_MIN": SUMMER_ELIGIBLE_MIN,
            "SUMMER_ELIGIBLE_MAX": SUMMER_ELIGIBLE_MAX,
            "FAIL_HARD_BLOCK_THRESHOLD": FAIL_HARD_BLOCK_THRESHOLD,
            "MAX_SUMMER_CLASSES": MAX_SUMMER_CLASSES,
        },
        "micro_rules": [
            {
                "name": "pass",
                "label": "Réussite",
                "threshold_min": PASS_THRESHOLD,
                "threshold_max": None,
                "outcome_state": "PASS",
                "outcome_label": "Cours réussi",
                "color": "green",
                "note": None,
            },
            {
                "name": "teacher_review",
                "label": "Révision Enseignant",
                "threshold_min": TEACHER_REVIEW_MIN,
                "threshold_max": TEACHER_REVIEW_MAX,
                "outcome_state": "TEACHER_REVIEW_PENDING",
                "outcome_label": "En attente de révision enseignant",
                "color": "orange",
                "note": "Priorité absolue — écrase toutes les autres règles macro",
            },
            {
                "name": "summer_eligible",
                "label": "Éligible École d'Été",
                "threshold_min": SUMMER_ELIGIBLE_MIN,
                "threshold_max": SUMMER_ELIGIBLE_MAX,
                "outcome_state": "SUMMER_ELIGIBLE",
                "outcome_label": "Routage vers l'école d'été",
                "color": "yellow",
                "note": "Cours de base/sanctionnés seulement. Cours non-sanctionné dans cette plage → FAILED.",
            },
            {
                "name": "hard_fail",
                "label": "Échec Bloquant",
                "threshold_min": None,
                "threshold_max": FAIL_HARD_BLOCK_THRESHOLD - 1,
                "outcome_state": "FAILED",
                "outcome_label": "Échec dur — aucune récupération par école d'été",
                "color": "red",
                "note": "Note strictement inférieure à 50. Déclenche la politique de niveau.",
            },
        ],
        "precedence": [
            {
                "order": 1,
                "rule_key": "TEACHER_REVIEW_PRIORITY",
                "label": "Révision Enseignant",
                "trigger": f"Au moins un cours dans la plage {TEACHER_REVIEW_MIN}–{TEACHER_REVIEW_MAX}",
                "outcome_workflow": "REGULAR_REVIEW_PENDING",
                "outcome_label": "Dossier en révision manuelle",
                "note": "Bloque toutes les règles suivantes — évalué en premier absolu",
            },
            {
                "order": 2,
                "rule_key": "SUMMER_ROUTING",
                "label": "Routage École d'Été",
                "trigger": f"Au moins un cours éligible ({SUMMER_ELIGIBLE_MIN}–{SUMMER_ELIGIBLE_MAX}) ET aucun échec",
                "outcome_workflow": "READY_FOR_FINALIZATION",
                "outcome_label": "Promotion avec passage par l'école d'été",
                "note": "Ne s'applique que si aucun cours n'est en échec",
            },
            {
                "order": 3,
                "rule_key": "LEVEL_POLICY",
                "label": "Politique par Niveau",
                "trigger": "Aucune des règles précédentes n'est déclenchée",
                "outcome_workflow": "(selon niveau de l'élève)",
                "outcome_label": "Délégué à la politique spécifique au niveau",
                "note": None,
            },
        ],
        "level_policies": [
            {
                "level_key": "SEC_1",
                "label": "Secondaire 1",
                "description": "Politique clémente — un échec standard mène à la reprise (holdback), pas à l'IFP",
                "rules": [
                    {
                        "priority": 1,
                        "condition": f"Au moins un cours avec note < {FAIL_HARD_BLOCK_THRESHOLD} (échec dur)",
                        "outcome_workflow": "IFP_CANDIDATE_REVIEW",
                        "outcome_final": None,
                        "rule_key": "HARD_FAILURE",
                        "label": "Candidature IFP",
                    },
                    {
                        "priority": 2,
                        "condition": f"Au moins un cours en échec standard (≥ {FAIL_HARD_BLOCK_THRESHOLD})",
                        "outcome_workflow": "READY_FOR_FINALIZATION",
                        "outcome_final": "APRIL_FINAL_HOLDBACK",
                        "rule_key": "LEVEL_SEC_1_HOLDBACK",
                        "label": "Reprise (Redoublement)",
                    },
                    {
                        "priority": 3,
                        "condition": "Tous les cours réussis",
                        "outcome_workflow": "READY_FOR_FINALIZATION",
                        "outcome_final": "APRIL_FINAL_PROMOTE_REGULAR",
                        "rule_key": "LEVEL_AUTO_PROMOTE",
                        "label": "Promotion Régulière",
                    },
                ],
            },
            {
                "level_key": "SEC_4",
                "label": "Secondaire 4",
                "description": "Politique stricte — tout échec (quelle que soit la sévérité) déclenche une révision IFP",
                "rules": [
                    {
                        "priority": 1,
                        "condition": "Au moins un cours en échec (toute sévérité)",
                        "outcome_workflow": "IFP_CANDIDATE_REVIEW",
                        "outcome_final": None,
                        "rule_key": "LEVEL_SEC_4_IFP",
                        "label": "Candidature IFP",
                    },
                    {
                        "priority": 2,
                        "condition": "Tous les cours réussis",
                        "outcome_workflow": "READY_FOR_FINALIZATION",
                        "outcome_final": "APRIL_FINAL_PROMOTE_REGULAR",
                        "rule_key": "LEVEL_AUTO_PROMOTE",
                        "label": "Promotion Régulière",
                    },
                ],
            },
            {
                "level_key": "DEFAULT",
                "label": "Autres niveaux (Sec 2, Sec 3, Sec 5)",
                "description": "Politique conservatrice par défaut — tout échec entraîne une révision IFP",
                "rules": [
                    {
                        "priority": 1,
                        "condition": "Au moins un cours en échec",
                        "outcome_workflow": "IFP_CANDIDATE_REVIEW",
                        "outcome_final": None,
                        "rule_key": "HARD_FAILURE",
                        "label": "Candidature IFP (défaut)",
                    },
                    {
                        "priority": 2,
                        "condition": "Tous les cours réussis",
                        "outcome_workflow": "READY_FOR_FINALIZATION",
                        "outcome_final": "APRIL_FINAL_PROMOTE_REGULAR",
                        "rule_key": "AUTO_PROMOTE",
                        "label": "Promotion Régulière",
                    },
                ],
            },
        ],
    }
