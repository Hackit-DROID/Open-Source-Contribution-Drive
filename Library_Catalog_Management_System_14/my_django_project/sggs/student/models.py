

from django.db import models

class Student(models.Model):
    regno = models.CharField(max_length=20, unique=True)   # Registration Number
    name = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    year = models.IntegerField()
    cet = models.FloatField()   # assuming CET is a score/marks

    def __str__(self):
        return f"{self.regno} - {self.name}"

