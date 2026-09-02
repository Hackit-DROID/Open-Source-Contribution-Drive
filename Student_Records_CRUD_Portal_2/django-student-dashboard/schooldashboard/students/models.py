from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=100)
    regno = models.CharField(max_length=20)
    student_class = models.CharField(max_length=10)
    branch = models.CharField(max_length=50)
    year = models.IntegerField()
    sub = models.CharField(max_length=50)
    marks = models.IntegerField()
    grade = models.CharField(max_length=2)
    college = models.CharField(max_length=100)

    def __str__(self):
        return self.name
