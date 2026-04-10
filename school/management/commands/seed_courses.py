import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from school.models import Course

class Command(BaseCommand):
    help = 'Peuple la table Course à partir du fichier JSON courses_seed.json à la racine'

    def handle(self, *args, **options):
        # Le fichier est à la racine du projet
        file_path = os.path.join(settings.BASE_DIR, 'courses_seed.json')

        if not os.path.exists(file_path):
            raise CommandError(f"Le fichier de données est introuvable à la racine : {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                courses_data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Erreur de lecture du JSON : {str(e)}")

        count = 0
        for item in courses_data:
            # Gestion des valeurs nulles pour les périodes (si null -> 0)
            periods_val = item.get('periods') or 0

            # On utilise update_or_create pour assurer l'idempotence
            course, created = Course.objects.update_or_create(
                local_code=item['local_code'],
                defaults={
                    'meq_code': item.get('meq_code'),
                    'description': item['description'],
                    'level': item.get('level'),
                    'credits': periods_val,  # Règle d'affaires : Crédits = Périodes
                    'periods': periods_val,
                    'is_core_or_sanctioned': item.get('is_core_or_sanctioned', False),
                    'is_active': True
                }
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} courses from root file. Credits updated."))
