from django.db import models


class Student(models.Model):
    regno = models.CharField(max_length=20, unique=True)   # Registration number
    name = models.CharField(max_length=200)
    branch = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()              # e.g., 1, 2, 3, 4
    cet = models.FloatField()                              # CET score

    def __str__(self):
        return f"{self.regno} - {self.name}"
