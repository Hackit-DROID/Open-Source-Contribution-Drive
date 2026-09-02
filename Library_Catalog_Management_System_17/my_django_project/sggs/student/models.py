from django.db import models

class Student(models.Model):   # <- Capitalized class name
    regno = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    year = models.IntegerField()
    cet = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.regno} - {self.name}"
