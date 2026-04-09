from django.core.management.base import BaseCommand
from school.models import Course

class Command(BaseCommand):
    help = 'Supprime les "Cours Fantômes" créés par erreur lors de l\'ingestion (Codes MEQ à 6 chiffres)'

    def handle(self, *args, **options):
        # Détection basée sur la signature des cours créés par erreur
        ghosts = Course.objects.filter(
            meq_code__isnull=True,
            local_code__regex=r'^\d{6}$',
            periods=0,
            level__isnull=True
        )

        count = ghosts.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("Aucun cours fantôme détecté."))
            return

        self.stdout.write(self.style.WARNING(f"Détection de {count} cours fantômes..."))

        for course in ghosts:
            self.stdout.write(f"Suppression du cours fantôme : {course.local_code} - {course.description}")
            course.delete()

        self.stdout.write(self.style.SUCCESS(f"Nettoyage terminé. {count} cours supprimés (incluant offres et résultats liés)."))
