import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from students.models import Student, AcademicResult
from school.models import Course, Teacher, CourseOffering

class Command(BaseCommand):
    help = "Importe les crédits historiques à partir d'un fichier CSV GPI (basé sur les codes MEQ)"

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help="Chemin vers le fichier CSV")
        parser.add_argument(
            '--year', 
            type=str, 
            default="2024-2025", 
            help="Année scolaire cible (ex: 2024-2025)"
        )

    def handle(self, *args, **options):
        file_path = options['csv_file']
        academic_year = options['year']

        if not os.path.exists(file_path):
            raise CommandError(f"Le fichier {file_path} n'existe pas.")

        stats = {
            'results_imported': 0,
            'students_updated': 0,
            'unknown_meq_codes': set(),
            'skipped_rows': 0
        }

        try:
            # On utilise utf-8-sig pour gérer le BOM Excel potentiel
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=',')
                
                with transaction.atomic():
                    for row_idx, row in enumerate(reader, start=2):
                        try:
                            # Nettoyage des clés (au cas où il y aurait des espaces dans le CSV)
                            row = {k.strip(): v for k, v in row.items() if k}
                            
                            fiche = row.get('Fiche')
                            meq_code = row.get('Matière')
                            raw_grade = row.get('Som. Final')
                            full_name = row.get('Nom et prénom', 'Nom inconnu')

                            if not fiche or not meq_code:
                                stats['skipped_rows'] += 1
                                continue

                            # 1. Gestion de la note
                            grade = None
                            if raw_grade and raw_grade.strip():
                                try:
                                    grade = int(float(raw_grade.strip()))
                                except ValueError:
                                    grade = None

                            # 2. Recherche du cours (Master Data)
                            course = Course.objects.filter(meq_code=meq_code.strip()).first()
                            
                            if not course:
                                stats['unknown_meq_codes'].add(meq_code)
                                continue

                            # 3. Synchronisation de l'élève
                            student, created = Student.objects.get_or_create(
                                fiche=int(float(fiche)),
                                defaults={'full_name': full_name, 'is_active': True}
                            )
                            if created: stats['students_updated'] += 1

                            # 4. Création de l'offre "Pont" (HIST)
                            offering, _ = CourseOffering.objects.get_or_create(
                                course=course,
                                group_number="HIST",
                                academic_year=academic_year,
                                defaults={'is_active': False}
                            )

                            # 5. Enregistrement du résultat
                            AcademicResult.objects.update_or_create(
                                student=student,
                                offering=offering,
                                defaults={
                                    'academic_year': academic_year,
                                    'final_grade': grade
                                }
                            )
                            stats['results_imported'] += 1

                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Erreur ligne {row_idx}: {str(e)}"))
                            stats['skipped_rows'] += 1

        except Exception as e:
            raise CommandError(f"Erreur lors de l'ouverture du fichier : {str(e)}")

        # --- Rapport final ---
        self.stdout.write(self.style.SUCCESS("\n--- Rapport d'importation historique ---"))
        self.stdout.write(f"Année traitée : {academic_year}")
        self.stdout.write(f"Résultats importés/mis à jour : {stats['results_imported']}")
        self.stdout.write(f"Nouveaux élèves créés : {stats['students_updated']}")
        
        if stats['unknown_meq_codes']:
            self.stdout.write(self.style.WARNING(f"Codes MEQ introuvables ({len(stats['unknown_meq_codes'])}) :"))
            codes = sorted(list(stats['unknown_meq_codes']))
            self.stdout.write(", ".join(codes[:15]) + ("..." if len(codes) > 15 else ""))
        
        if stats['skipped_rows']:
            self.stdout.write(self.style.NOTICE(f"Lignes ignorées (données manquantes) : {stats['skipped_rows']}"))
