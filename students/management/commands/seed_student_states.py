from django.core.management.base import BaseCommand
from students.models import Student
from students.services.state_seeder import seed_student_state

class Command(BaseCommand):
    help = "Seeds StudentState records for all active students from existing data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--year", 
            type=str, 
            required=True, 
            help="Academic year to seed (e.g., 2025-2026)"
        )

    def handle(self, *args, **options):
        academic_year = options["year"]
        active_students = Student.objects.filter(is_active=True)
        count = 0

        for student in active_students:
            seed_student_state(student, academic_year)
            count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {count} student states for {academic_year}")
        )
