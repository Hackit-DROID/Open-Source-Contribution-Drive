
from django.db import models

class Student(models.Model):
    reg_no = models.CharField(max_length=20, primary_key=True)  # Primary Key
    student_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    math = models.IntegerField()
    phy = models.IntegerField()
    chem = models.IntegerField()

    def __str__(self):
        return f"{self.student_name} ({self.reg_no})"
