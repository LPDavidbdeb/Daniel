from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ImportLog(models.Model):
    IMPORT_TYPES = [
        ('ELEVES', 'Élèves'),
        ('RESULTATS', 'Résultats'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    import_type = models.CharField(max_length=20, choices=IMPORT_TYPES)
    filename = models.CharField(max_length=255)
    academic_year = models.CharField(max_length=9, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    dry_run = models.BooleanField(default=False)
    
    # Impact stats (stored as JSON)
    stats = models.JSONField()
    
    # Error log
    errors = models.JSONField(default=list)

    def __str__(self):
        return f"{self.import_type} - {self.filename} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
