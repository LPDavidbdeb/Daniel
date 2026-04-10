from django.core.management.base import BaseCommand
from django.db import transaction
from school.models import Course

class Command(BaseCommand):
    help = 'Supprime définitivement les cours invalides (sans niveau et sans périodes)'

    def handle(self, *args, **options):
        # Signature des cours invalides : Pas de niveau défini ET 0 périodes
        invalid_courses = Course.objects.filter(
            level__isnull=True,
            periods=0
        )

        count = invalid_courses.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("Aucun cours invalide détecté. La base est propre."))
            return

        self.stdout.write(self.style.WARNING(f"Détection de {count} cours invalides..."))
        
        # On liste les codes pour traçabilité
        codes = list(invalid_courses.values_list('local_code', flat=True))
        self.stdout.write(f"Codes à supprimer : {', '.join(codes)}")

        with transaction.atomic():
            invalid_courses.delete()

        self.stdout.write(self.style.SUCCESS(f"Nettoyage terminé avec succès. {count} cours supprimés."))
