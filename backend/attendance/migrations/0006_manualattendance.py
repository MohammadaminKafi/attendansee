# Generated migration for ManualAttendance model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('attendance', '0005_student_profile_picture'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManualAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_present', models.BooleanField(default=True, help_text='Whether the student is marked as present or absent')),
                ('marked_at', models.DateTimeField(auto_now=True)),
                ('note', models.TextField(blank=True, default='', help_text='Optional note about the manual attendance marking')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('marked_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='manual_attendance_marks', to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='manual_attendance_records', to='attendance.session')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='manual_attendance_records', to='attendance.student')),
            ],
            options={
                'verbose_name': 'Manual Attendance',
                'verbose_name_plural': 'Manual Attendance Records',
                'db_table': 'manual_attendance',
                'ordering': ['-marked_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='manualattendance',
            constraint=models.UniqueConstraint(fields=('student', 'session'), name='unique_manual_attendance_per_session'),
        ),
        migrations.AddIndex(
            model_name='manualattendance',
            index=models.Index(fields=['student', 'session'], name='manual_atte_student_6c4a5f_idx'),
        ),
        migrations.AddIndex(
            model_name='manualattendance',
            index=models.Index(fields=['session', '-marked_at'], name='manual_atte_session_3a8f21_idx'),
        ),
        migrations.AddIndex(
            model_name='manualattendance',
            index=models.Index(fields=['is_present'], name='manual_atte_is_pres_d52b89_idx'),
        ),
    ]
