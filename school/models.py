from django.db import models
from django.conf import settings

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.CharField(max_length=255)
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
    academic_year = models.CharField(max_length=9, db_index=True, default="2023-2024")
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
        return f"{self.course.code} ({self.group_number}) [{self.academic_year}]"
