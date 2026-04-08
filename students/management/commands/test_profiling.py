from django.core.management.base import BaseCommand
from students.models import Student
from students.services import StudentProfilingService

class Command(BaseCommand):
    help = 'Teste le service de profilage académique sur les 5 premiers élèves actifs'

    def handle(self, *args, **options):
        # On récupère les 5 premiers élèves actifs
        students = Student.objects.filter(is_active=True)[:5]
        
        if not students.exists():
            self.stdout.write(self.style.WARNING("Aucun élève actif trouvé. Veuillez d'abord importer les élèves et les résultats."))
            return

        self.stdout.write(self.style.SUCCESS("-" * 85))
        self.stdout.write(self.style.SUCCESS(f"{'Nom de l''élève':<35} | {'Moyenne':<8} | {'Échecs':<8} | {'Profil':<20}"))
        self.stdout.write(self.style.SUCCESS("-" * 85))

        for student in students:
            avg = StudentProfilingService.calculate_student_average(student)
            failures = StudentProfilingService.get_failed_courses(student)
            profile = StudentProfilingService.determine_academic_profile(student)
            
            avg_str = f"{avg}%" if avg is not None else "N/A"
            failures_str = str(len(failures))
            
            self.stdout.write(f"{student.full_name:<35} | {avg_str:<8} | {failures_str:<8} | {profile:<20}")
        
        self.stdout.write(self.style.SUCCESS("-" * 85))
