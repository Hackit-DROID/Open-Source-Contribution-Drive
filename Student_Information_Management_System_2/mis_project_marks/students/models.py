from django.db import models

class Student(models.Model):
    regno = models.AutoField(primary_key=True)  # regno as Primary Key
    student_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    phy = models.IntegerField()
    chem = models.IntegerField()
    math = models.IntegerField()

    def average(self):
        """Returns the average marks of the student"""
        return (self.phy + self.chem + self.math) / 3

    def __str__(self):
        return f"{self.regno} - {self.student_name}"
