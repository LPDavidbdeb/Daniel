from django.contrib import admin
from .models import Student, AcademicResult, StudentPromotionOverride

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('fiche', 'full_name', 'level', 'current_group', 'is_active')
    list_filter = ('level', 'current_group', 'is_active')
    search_fields = ('fiche', 'full_name', 'permanent_code')

@admin.register(AcademicResult)
class AcademicResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'get_course', 'final_grade', 'academic_year')
    list_filter = ('academic_year',)
    search_fields = ('student__full_name', 'offering__course__local_code')

    def get_course(self, obj):
        return obj.offering.course.local_code
    get_course.short_description = 'Cours'

@admin.register(StudentPromotionOverride)
class StudentPromotionOverrideAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'academic_year', 'override_type', 'created_at', 'created_by')
    list_filter = ('academic_year', 'override_type')
    search_fields = ('student__full_name', 'course__local_code')
