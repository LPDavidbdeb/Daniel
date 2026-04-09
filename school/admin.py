from django.contrib import admin
from .models import Course, Teacher, CourseOffering

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'description', 'level', 'credits', 'is_core_or_sanctioned', 'is_active')
    list_filter = ('level', 'is_core_or_sanctioned', 'is_active')
    search_fields = ('code', 'description')

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
