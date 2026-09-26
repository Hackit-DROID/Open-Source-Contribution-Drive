from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faculty', '0003_remove_faculty_designation_remove_faculty_students'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='faculty',
            index=models.Index(fields=['department'], name='faculty_department_idx'),
        ),
    ]
