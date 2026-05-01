from django.db import models
from django.conf import settings

class Student(models.Model):
    fiche = models.IntegerField(primary_key=True)
    permanent_code = models.CharField(max_length=12, unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    level = models.CharField(max_length=50)
    current_group = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.full_name} ({self.fiche})"

class AcademicResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    offering = models.ForeignKey(
        'school.CourseOffering', 
        on_delete=models.CASCADE, 
        related_name='results',
        null=True,
        blank=True
    )
    academic_year = models.CharField(max_length=9, db_index=True, default="2025-2026")

    step_1_grade = models.IntegerField(null=True, blank=True)
    step_2_grade = models.IntegerField(null=True, blank=True)
    final_grade = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'offering')
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['academic_year']),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.offering.course.local_code} ({self.academic_year})"

class SummerSchoolEnrollment(models.Model):
    """One summer school course per student per academic year."""
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='summer_school_enrollments'
    )
    course = models.ForeignKey(
        'school.Course', on_delete=models.CASCADE, related_name='summer_school_enrollments'
    )
    academic_year = models.CharField(max_length=9, db_index=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='summer_school_enrollments'
    )

    class Meta:
        unique_together = ('student', 'academic_year')  # one course per student per year

    def __str__(self):
        return f"Été: {self.student.full_name} → {self.course.local_code} ({self.academic_year})"


class StudentPromotionOverride(models.Model):
    TYPES = [
        ('FORCE_PASS', 'Passage Forcé'),
        ('FORCE_RETAKE', 'Reprise Forcée'),
        ('TRANSFER_IFP', 'Transfert IFP'),
        ('TRANSFER_DIM', 'Transfert DIM'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='overrides')
    course = models.ForeignKey('school.Course', on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9, db_index=True)
    override_type = models.CharField(max_length=20, choices=TYPES)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('student', 'course', 'academic_year')

    def __str__(self):
        return f"Dérogration: {self.student.full_name} - {self.course.local_code} ({self.academic_year})"
