import unicodedata
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from students.models import AcademicResult
from school.models import Course, Teacher, CourseOffering

User = get_user_model()

def slugify_name(name):
    """Nettoie les noms pour les emails (ex: 'Émile' -> 'emile')"""
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[^\w\s-]', '', name).strip().lower()
    return re.sub(r'[-\s]+', '.', name)

class Command(BaseCommand):
    help = 'Migre les données des cours et transforme les enseignants en Utilisateurs'

    def handle(self, *args, **options):
        results = AcademicResult.objects.all()
        total = results.count()
        
        if total == 0:
            self.stdout.write("Aucun résultat à traiter.")
            return

        # 1. Préparer le groupe Enseignants
        teacher_group, _ = Group.objects.get_or_create(name='Professeurs')

        with transaction.atomic():
            created_courses = 0
            created_users = 0
            created_offerings = 0

            for res in results:
                # 1. Gérer le cours
                course, created = Course.objects.get_or_create(
                    local_code=res.course_code,
                    defaults={'description': res.course_description}
                )
                if created: created_courses += 1

                # 2. Gérer l'enseignant (Transformation en User)
                teacher = None
                if res.teacher_name:
                    # On cherche si le profil enseignant existe déjà
                    teacher = Teacher.objects.filter(full_name=res.teacher_name).first()
                    
                    if not teacher:
                        # Parsing du nom (Prénom Nom)
                        parts = res.teacher_name.split(' ', 1)
                        first_name = parts[0]
                        last_name = parts[1] if len(parts) > 1 else ""
                        
                        # Génération email fictif
                        email = f"{slugify_name(first_name)}.{slugify_name(last_name)}@csspi.qc.ca"
                        
                        # Création de l'utilisateur
                        user, user_created = User.objects.get_or_create(
                            email=email,
                            defaults={
                                'first_name': first_name,
                                'last_name': last_name,
                                'is_active': True
                            }
                        )
                        if user_created:
                            user.set_unusable_password()
                            user.groups.add(teacher_group)
                            user.save()
                            created_users += 1
                        
                        # Création du profil Teacher lié
                        teacher = Teacher.objects.create(
                            user=user,
                            full_name=res.teacher_name
                        )

                # 3. Gérer l'offre de cours
                offering, created = CourseOffering.objects.get_or_create(
                    course=course,
                    group_number=res.course_group,
                    defaults={'teacher': teacher}
                )
                if created: created_offerings += 1

                # 4. Lier le résultat
                res.offering = offering
                res.save()

        self.stdout.write(self.style.SUCCESS("Normalisation 3NF avec Utilisateurs terminée !"))
        self.stdout.write(f"- Cours : {created_courses}")
        self.stdout.write(f"- Utilisateurs (Profs) : {created_users}")
        self.stdout.write(f"- Groupes-Cours : {created_offerings}")
