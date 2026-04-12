from django.db.models import Avg
from ..models import Student

class StudentProfilingService:
    @staticmethod
    def calculate_student_average(student: Student) -> float | None:
        """Calcule la moyenne globale de l'élève basée sur final_grade (Som. Final)."""
        results = student.results.filter(final_grade__isnull=False)
        if not results.exists():
            return None
        
        avg = results.aggregate(Avg('final_grade'))['final_grade__avg']
        return round(float(avg), 2) if avg is not None else None

    @staticmethod
    def get_failed_courses(student: Student, passing_grade: int = 60) -> list[str]:
        """Retourne la liste des codes de cours (Matière) en échec."""
        # Correction 3NF : course_code est maintenant dans offering__course__local_code
        failed_results = student.results.filter(final_grade__lt=passing_grade)
        return list(failed_results.values_list('offering__course__local_code', flat=True))

    @staticmethod
    def count_sanctioned_passed(student: Student, academic_year: str = "2025-2026") -> int:
        """Nombre de cours de base/sanctionnés réussis (≥ 60) pour l'année donnée."""
        return student.results.filter(
            academic_year=academic_year,
            final_grade__gte=60,
            offering__course__is_core_or_sanctioned=True,
        ).count()

    @staticmethod
    def determine_academic_profile(student: Student) -> str:
        """Détermine le profil académique de l'élève."""
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
