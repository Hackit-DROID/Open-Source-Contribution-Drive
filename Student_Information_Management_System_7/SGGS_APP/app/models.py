from django.db import models

# Create your models here.
class Student(models.Model):
    regno = models.AutoField(primary_key=True)
    student_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    phy = models.IntegerField()
    chem = models.IntegerField()
    math = models.IntegerField()


    def __str__(self):
        return f"{self.regno} - {self.student_name}"