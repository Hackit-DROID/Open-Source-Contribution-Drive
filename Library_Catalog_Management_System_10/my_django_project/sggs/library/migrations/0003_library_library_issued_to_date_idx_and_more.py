from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0002_alter_library_issued_to'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='library',
            index=models.Index(fields=['issued_to', 'issued_date'], name='library_issued_to_date_idx'),
        ),
        migrations.AddIndex(
            model_name='library',
            index=models.Index(fields=['title'], name='library_title_idx'),
        ),
        migrations.AddIndex(
            model_name='library',
            index=models.Index(fields=['author'], name='library_author_idx'),
        ),
    ]
