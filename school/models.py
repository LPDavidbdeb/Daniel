from django.db import models
from django.conf import settings

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.CharField(max_length=255)
    level = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Année du secondaire (1 à 5)"
    )
    credits = models.IntegerField(
        default=0, 
        help_text="Nombre de crédits associés au cours"
    )
    is_core_or_sanctioned = models.BooleanField(
        default=False, 
        help_text="Vrai pour les matières de base bloquantes comme le français ou les mathématiques, ou les matières sanctionnées par le MEQ"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.description}"

class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='teacher_profile'
    )
    full_name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name

class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='offerings')
    group_number = models.CharField(max_length=10)
    academic_year = models.CharField(max_length=9, db_index=True, default="2025-2026")
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='offerings'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('course', 'group_number', 'academic_year')

    def __str__(self):
        return f"{self.course.code} ({self.group_number}) [{self.academic_year}]"
