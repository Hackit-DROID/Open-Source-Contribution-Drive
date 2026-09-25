from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_no = models.CharField(max_length=20, unique=True)
    branch = models.CharField(max_length=50, null=True, blank=True)
    physics = models.FloatField(default=0)
    chemistry = models.FloatField(default=0)
    maths = models.FloatField(default=0)

    def __str__(self):
        return f"{self.name} ({self.roll_no})"
