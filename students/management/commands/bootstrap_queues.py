from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Prefetch
from students.models import Student, StudentState, AcademicResult, StudentPromotionOverride
from students.services.auto_derivation import derive_student_state
from students.enums import WorkflowState, VettingStatus

class Command(BaseCommand):
    help = "Force a complete re-evaluation of all active students to populate the StudentState ledger and review queues."

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=str,
            default='2025-2026',
            help='Academic year to process (default: 2025-2026)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the process without saving to the database'
        )

    def handle(self, *args, **options):
        academic_year = options['year']
        dry_run = options['dry_run']

        self.stdout.write(self.style.NOTICE(f"--- Bootstrapping queues for {academic_year} ---"))

        # 1. Fetch active students with necessary prefetching to avoid N+1
        students = Student.objects.filter(is_active=True).prefetch_related(
            Prefetch(
                'results', 
                queryset=AcademicResult.objects.filter(academic_year=academic_year).select_related('offering__course')
            ),
            Prefetch(
                'overrides',
                queryset=StudentPromotionOverride.objects.filter(academic_year=academic_year).select_related('course')
            )
        )

        total_count = students.count()
        self.stdout.write(f"Found {total_count} active students.")

        stats = {
            "IFP_CANDIDATE_REVIEW": 0,
            "TEACHER_REVIEW": 0,
            "SUMMER_ROUTING": 0,
            "AUTO_VETTED": 0,
            "REGULAR_REVIEW_PENDING": 0,
            "ERRORS": 0
        }

        with transaction.atomic():
            for student in students:
                try:
                    # 2. Derive state based on business rules
                    derivation = derive_student_state(student, academic_year)
                    
                    # 3. Categorize for stats
                    w_state = derivation["workflow_state"]
                    v_status = derivation["vetting_status"]
                    
                    if w_state == WorkflowState.IFP_CANDIDATE_REVIEW:
                        stats["IFP_CANDIDATE_REVIEW"] += 1
                    elif w_state == WorkflowState.REGULAR_REVIEW_PENDING:
                        # Distinguish between Teacher Review and Summer based on reason/grades
                        msg = derivation["reason_codes"].get("message", "")
                        if "57-59" in msg:
                            stats["TEACHER_REVIEW"] += 1
                        else:
                            stats["REGULAR_REVIEW_PENDING"] += 1
                    elif w_state == WorkflowState.READY_FOR_FINALIZATION:
                        if v_status == VettingStatus.AUTO_VETTED:
                            # Check if it's summer routing (FinalAprilState is set)
                            if derivation.get("final_april_state") == "APRIL_FINAL_PROMOTE_WITH_SUMMER":
                                stats["SUMMER_ROUTING"] += 1
                            else:
                                stats["AUTO_VETTED"] += 1
                        else:
                            stats["AUTO_VETTED"] += 1

                    # 4. Persistence
                    if not dry_run:
                        StudentState.objects.update_or_create(
                            student=student,
                            academic_year=academic_year,
                            defaults={
                                "workflow_state": derivation["workflow_state"],
                                "final_april_state": derivation.get("final_april_state"),
                                "vetting_status": derivation["vetting_status"],
                                "reason_codes": derivation["reason_codes"]
                            }
                        )

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing {student.fiche}: {str(e)}"))
                    stats["ERRORS"] += 1

        # 5. Final Report
        self.stdout.write(self.style.SUCCESS("\n--- Bootstrap Complete ---"))
        self.stdout.write(f"Analyzed {total_count} students.")
        self.stdout.write(self.style.NOTICE(f"- Routed to IFP Queue: {stats['IFP_CANDIDATE_REVIEW']}"))
        self.stdout.write(self.style.NOTICE(f"- Routed to Teacher Review (57-59): {stats['TEACHER_REVIEW']}"))
        self.stdout.write(self.style.NOTICE(f"- Routed to Summer Routing (50-59): {stats['SUMMER_ROUTING']}"))
        self.stdout.write(self.style.NOTICE(f"- Auto-Vetted / Resolved: {stats['AUTO_VETTED']}"))
        self.stdout.write(self.style.NOTICE(f"- Other Review Pending: {stats['REGULAR_REVIEW_PENDING']}"))
        
        if stats["ERRORS"] > 0:
            self.stdout.write(self.style.ERROR(f"- Processing Errors: {stats['ERRORS']}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: No changes were saved to the database."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully updated StudentState for {total_count - stats['ERRORS']} students."))
