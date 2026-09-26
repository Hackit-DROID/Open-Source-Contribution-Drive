from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_rename_due_amount_account_due_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='account',
            index=models.Index(fields=['student', 'library'], name='account_student_library_idx'),
        ),
        migrations.AddIndex(
            model_name='account',
            index=models.Index(fields=['due'], name='account_due_idx'),
        ),
    ]
