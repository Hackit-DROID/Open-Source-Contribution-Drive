from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0005_student_branch_alter_student_chemistry_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='student',
            index=models.Index(fields=['branch'], name='student_branch_idx'),
        ),
        migrations.AddIndex(
            model_name='student',
            index=models.Index(fields=['name'], name='student_name_idx'),
        ),
        migrations.AddIndex(
            model_name='student',
            index=models.Index(fields=['-physics'], name='student_physics_desc_idx'),
        ),
        migrations.AddIndex(
            model_name='student',
            index=models.Index(fields=['-chemistry'], name='student_chemistry_desc_idx'),
        ),
        migrations.AddIndex(
            model_name='student',
            index=models.Index(fields=['-maths'], name='student_maths_desc_idx'),
        ),
    ]
