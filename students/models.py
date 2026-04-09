from django.db import models

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
    offering = models.ForeignKey('school.CourseOffering', on_delete=models.CASCADE, related_name='results')
    
    step_1_grade = models.IntegerField(null=True, blank=True)
    step_2_grade = models.IntegerField(null=True, blank=True)
    final_grade = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'offering')

    def __str__(self):
        return f"{self.student.full_name} - {self.offering.course.code} ({self.final_grade or 'N/A'})"
