import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from school.models import MeqReference


class Command(BaseCommand):
    help = "Seed la table MeqReference depuis le fixture JSON officiel."

    def handle(self, *args, **options):
        fixture_path = Path(settings.BASE_DIR) / "school" / "fixtures" / "meq_reference_seed.json"

        if not fixture_path.exists():
            self.stderr.write(self.style.ERROR(f"Fichier introuvable: {fixture_path}"))
            return

        with fixture_path.open("r", encoding="utf-8") as fixture_file:
            payload = json.load(fixture_file)

        created_count = 0
        updated_count = 0

        for item in payload:
            _, created = MeqReference.objects.update_or_create(
                meq_code=item["meq_code"],
                defaults={
                    "description": item["description"],
                    "credits": item["credits"],
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        total = MeqReference.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"MEQ seed termine: {created_count} crees, {updated_count} mis a jour, total={total}."
            )
        )

