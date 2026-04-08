from django.db.models import Avg
from .models import Student

class StudentProfilingService:
    @staticmethod
    def calculate_student_average(student: Student) -> float | None:
        """Calcule la moyenne globale de l'élève basée sur final_grade (Som. Final)."""
        # On utilise related_name='results' défini dans AcademicResult
        results = student.results.filter(final_grade__isnull=False)
        if not results.exists():
            return None
        
        # On agrège la moyenne via Django ORM
        avg = results.aggregate(Avg('final_grade'))['final_grade__avg']
        return round(float(avg), 2) if avg is not None else None

    @staticmethod
    def get_failed_courses(student: Student, passing_grade: int = 60) -> list[str]:
        """Retourne la liste des codes de cours (Matière) en échec."""
        failed_results = student.results.filter(final_grade__lt=passing_grade)
        return list(failed_results.values_list('course_code', flat=True))

    @staticmethod
    def determine_academic_profile(student: Student) -> str:
        """
        Détermine le profil académique de l'élève.
        Règles :
        - None : "Non évalué"
        - 2+ échecs : "En difficulté majeure"
        - 1 échec : "À risque (1 échec)"
        - 0 échec et Moyenne >= 85 : "Fort"
        - 0 échec et Moyenne 70-84 : "Moyen-Fort"
        - 0 échec et Moyenne 60-69 : "Fragile"
        """
        average = StudentProfilingService.calculate_student_average(student)
        failures = StudentProfilingService.get_failed_courses(student)
        num_failures = len(failures)

        if average is None:
            return "Non évalué"
        
        if num_failures >= 2:
            return "En difficulté majeure"
        
        if num_failures == 1:
            return "À risque (1 échec)"
        
        # 0 échec
        if average >= 85:
            return "Fort"
        if 70 <= average <= 84:
            return "Moyen-Fort"
        if 60 <= average <= 69:
            return "Fragile"
        
        return "Fragile"
