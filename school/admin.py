from django.contrib import admin
from .models import Course, Teacher, CourseOffering, Cohort

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('local_code', 'meq_code', 'description', 'level', 'credits', 'is_core_or_sanctioned', 'is_active')
    list_filter = ('level', 'is_core_or_sanctioned', 'is_active')
    search_fields = ('local_code', 'meq_code', 'description')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'get_email', 'is_active')
    search_fields = ('full_name', 'user__email')

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ('course', 'group_number', 'academic_year', 'teacher', 'is_active')
    list_filter = ('academic_year', 'is_active')

@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = ('name', 'cohort_type', 'academic_year', 'student_count', 'is_confirmed')
    list_filter = ('cohort_type', 'academic_year', 'is_confirmed')
    search_fields = ('name',)

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'Nb Élèves'
