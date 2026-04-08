from django.db import models

class Student(models.Model):
    fiche = models.IntegerField(primary_key=True)
    permanent_code = models.CharField(max_length=12, unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    level = models.CharField(max_length=50)  # Correspond à la "Classe" dans GPI
    current_group = models.CharField(max_length=50)  # Correspond au "Groupe-repère" dans GPI
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.full_name} ({self.fiche})"
