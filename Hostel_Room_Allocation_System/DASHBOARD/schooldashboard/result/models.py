from django.db import models

class Result(models.Model):
    student_name = models.CharField(max_length=100)
    regno = models.CharField(max_length=20)
    semester = models.IntegerField()
    subject = models.CharField(max_length=50)
    marks = models.IntegerField()
    grade = models.CharField(max_length=2)
    status = models.CharField(max_length=10, choices=[('Pass', 'Pass'), ('Fail', 'Fail')])

    def __str__(self):
        return f"{self.student_name} - Sem {self.semester}"
