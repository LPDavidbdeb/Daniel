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

class AcademicResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    course_code = models.CharField(max_length=20, db_index=True)  # GPI: "Matière"
    course_description = models.CharField(max_length=255)         # GPI: "Description de la matière"
    course_group = models.CharField(max_length=10)               # GPI: "Grp"
    teacher_name = models.CharField(max_length=255, null=True, blank=True) # GPI: "Nom et prénom de l'enseignant"
    step_1_grade = models.IntegerField(null=True, blank=True)    # GPI: "[1]"
    step_2_grade = models.IntegerField(null=True, blank=True)    # GPI: "[2]"
    final_grade = models.IntegerField(null=True, blank=True)     # GPI: "Som. Final"

    class Meta:
        unique_together = ('student', 'course_code')

    def __str__(self):
        return f"{self.student.full_name} - {self.course_code} ({self.final_grade or 'N/A'})"
