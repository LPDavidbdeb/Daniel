from django.db.models import Q
from students.models import AcademicResult, StudentPromotionOverride
from school.models import Course

class StudentEvaluator:
    """
    Moteur de classification et d'évaluation des élèves.
    Gère la logique métier complexe de promotion et d'accumulation de crédits.
    """
    
    PREDICTIVE_FAIL_THRESHOLD = 50
    MARGIN = 5  # Zone grise (45-54)
    MAX_CORE_FAILURES = 2
    SUCCESS_THRESHOLD = 60 # Règle historique/MEQ pour l'obtention des crédits

    @classmethod
    def get_accumulated_credits(cls, student, up_to_year: str) -> int:
        """
        Calcule le total des crédits accumulés jusqu'à une année donnée.
        Un cours donne ses crédits si la note finale >= 60 ou via dérogation FORCE_PASS.
        """
        # 1. On récupère tous les résultats historiques jusqu'à cette année incluse
        results = AcademicResult.objects.filter(
            student=student,
            academic_year__lte=up_to_year
        ).select_related('offering__course')

        # 2. On récupère les dérogations pour cet élève
        overrides = {
            (o.course_id, o.academic_year): o.override_type 
            for o in student.overrides.all()
        }

        # 3. Traitement des réussites avec dédoublonnage par code MEQ
        successful_meq_codes = set()
        total_credits = 0

        # On trie par année pour s'assurer que la première réussite valide les crédits
        for res in results.order_by('academic_year'):
            course = res.offering.course
            if not course.meq_code:
                continue
                
            # Vérification de la réussite
            is_success = False
            
            # Priorité 1: Dérogation
            override = overrides.get((course.id, res.academic_year))
            if override == 'FORCE_PASS':
                is_success = True
            elif override == 'FORCE_RETAKE':
                is_success = False
            # Priorité 2: Note réelle (>= 60)
            elif res.final_grade is not None and res.final_grade >= cls.SUCCESS_THRESHOLD:
                is_success = True

            if is_success and course.meq_code not in successful_meq_codes:
                successful_meq_codes.add(course.meq_code)
                total_credits += course.credits

        return total_credits

    @classmethod
    def evaluate_student_year(cls, student, academic_year: str) -> dict:
        """
        Analyse l'année en cours pour faire une prévision de classement.
        Basé sur un seuil prédictif de 50%.
        """
        # 1. Récupération des données
        results = AcademicResult.objects.filter(
            student=student,
            academic_year=academic_year
        ).select_related('offering__course')

        overrides = {
            o.course_id: o.override_type 
            for o in student.overrides.filter(academic_year=academic_year)
        }

        # 2. Variables de calcul
        total_credits_acc = cls.get_accumulated_credits(student, academic_year)
        potentiel_minimum = total_credits_acc
        credits_en_jeu = 0
        core_failures_count = 0
        borderline_count = 0
        total_subjects = results.count()

        for res in results:
            course = res.offering.course
            grade = res.final_grade
            
            # On applique la logique d'override
            is_fail = False
            override = overrides.get(course.id)
            
            if override == 'FORCE_RETAKE':
                is_fail = True
            elif override == 'FORCE_PASS':
                is_fail = False
            elif grade is not None:
                if grade < cls.PREDICTIVE_FAIL_THRESHOLD:
                    is_fail = True
                
                # Comptage de la zone grise (45-54)
                if (cls.PREDICTIVE_FAIL_THRESHOLD - cls.MARGIN) <= grade <= (cls.PREDICTIVE_FAIL_THRESHOLD + cls.MARGIN - 1):
                    borderline_count += 1

            if is_fail and course.is_core_or_sanctioned:
                core_failures_count += 1

            # Calcul des crédits "sauvables" (entre 50 et 59%)
            if grade is not None and 50 <= grade < 60:
                if override not in ['FORCE_PASS', 'FORCE_RETAKE']:
                    credits_en_jeu += course.credits

        potentiel_maximum = potentiel_minimum + credits_en_jeu

        # 3. Détermination de la recommandation
        recommendation = "PROMOTE"
        confidence = "HIGH"
        requires_review = False

        if core_failures_count >= cls.MAX_CORE_FAILURES:
            recommendation = "RETAIN"
        
        # Un transfert IFP pourrait être forcé par dérogation
        if any(ov == 'TRANSFER_IFP' for ov in overrides.values()):
            recommendation = "TRANSFER_IFP"

        # 4. Critères de révision (Humain)
        if borderline_count >= 1 or core_failures_count == 1:
            requires_review = True
            confidence = "LOW"

        return {
            "student_id": student.fiche,
            "academic_year": academic_year,
            "total_credits_accumulated": total_credits_acc,
            "potentiel_minimum": potentiel_minimum,
            "potentiel_maximum": potentiel_maximum,
            "credits_en_jeu": credits_en_jeu,
            "core_failures_count": core_failures_count,
            "borderline_count": borderline_count,
            "recommendation": recommendation,
            "confidence": confidence,
            "requires_review": requires_review
        }
