from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_no = models.CharField(max_length=20, unique=True)
    branch = models.CharField(max_length=50, null=True, blank=True)
    physics = models.FloatField(default=0)
    chemistry = models.FloatField(default=0)
    maths = models.FloatField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['branch'], name='student_branch_idx'),
            models.Index(fields=['name'], name='student_name_idx'),
            models.Index(fields=['-physics'], name='student_physics_desc_idx'),
            models.Index(fields=['-chemistry'], name='student_chemistry_desc_idx'),
            models.Index(fields=['-maths'], name='student_maths_desc_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.roll_no})"
