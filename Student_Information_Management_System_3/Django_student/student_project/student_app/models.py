from django.db import models

class Student(models.Model):
    regno = models.CharField(max_length=10, unique=True)
    student_name = models.CharField(max_length=50)
    branch = models.CharField(max_length=20)
    phy = models.IntegerField()
    chem = models.IntegerField()
    math = models.IntegerField()

    def __str__(self):
        return f"{self.regno} - {self.student_name}"
