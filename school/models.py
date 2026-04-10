from django.db import models
from django.conf import settings

class Course(models.Model):
    local_code = models.CharField(max_length=20, unique=True, db_index=True)
    meq_code = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        help_text="Code officiel du Ministère (MEQ)"
    )
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
    periods = models.IntegerField(
        default=0,
        help_text="Nombre de périodes dans l'horaire"
    )
    is_core_or_sanctioned = models.BooleanField(
        default=False, 
        help_text="Vrai pour les matières de base bloquantes comme le français ou les mathématiques, ou les matières sanctionnées par le MEQ"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.local_code} - {self.description}"


class MeqReference(models.Model):
    meq_code = models.CharField(max_length=10, primary_key=True)
    description = models.CharField(max_length=255)
    credits = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.meq_code} - {self.description}"

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
        # Un groupe-cours est unique pour une année donnée
        unique_together = ('course', 'group_number', 'academic_year')

    def __str__(self):
        return f"{self.course.local_code} ({self.group_number}) [{self.academic_year}]"

class Cohort(models.Model):
    TYPES = [
        ('ZENITH', 'Zénith'),
        ('IFP', 'IFP'),
        ('DIM', 'DIM'),
        ('ACCUEIL', 'Accueil'),
        ('PARCOURS', 'Parcours'),
    ]

    name = models.CharField(max_length=100)
    cohort_type = models.CharField(max_length=20, choices=TYPES)
    academic_year = models.CharField(max_length=9, db_index=True)
    min_capacity = models.IntegerField(default=15)
    max_capacity = models.IntegerField(default=32)
    is_confirmed = models.BooleanField(default=False)
    students = models.ManyToManyField('students.Student', related_name='cohorts', blank=True)

    class Meta:
        unique_together = ('name', 'academic_year')

    def __str__(self):
        return f"Cohorte: {self.name} ({self.academic_year})"
