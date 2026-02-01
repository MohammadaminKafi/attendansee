# Generated migration for adding profile_picture field to Student model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0004_rename_face_crops_embeddi_idx_face_crops_embeddi_7d6724_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='profile_picture',
            field=models.ImageField(
                blank=True,
                help_text='Optional profile picture for the student',
                max_length=500,
                null=True,
                upload_to='student_profiles/'
            ),
        ),
    ]
