from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0008_studentpromotionoverride'),
        ('school', '0009_course_classification'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SummerSchoolEnrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('academic_year', models.CharField(db_index=True, max_length=9)),
                ('enrolled_at', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='summer_school_enrollments',
                    to='school.course',
                )),
                ('enrolled_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='summer_school_enrollments',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='summer_school_enrollments',
                    to='students.student',
                )),
            ],
            options={
                'unique_together': {('student', 'academic_year')},
            },
        ),
    ]
