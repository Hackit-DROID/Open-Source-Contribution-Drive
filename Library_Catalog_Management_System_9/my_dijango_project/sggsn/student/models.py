from django.db import models

class Student(models.Model):
    regno = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    phy = models.IntegerField()
    chem = models.IntegerField()
    math = models.IntegerField()

    

    def __str__(self):
        return self.name

    @property
    def total(self):
        return self.phy + self.chem + self.math
