from django.db import models


class AccountStudent(models.Model):
    regno = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    branch = models.CharField(max_length=100)
    acc_id = models.IntegerField()
    fees = models.FloatField()

    def __str__(self):
        return f"{self.regno} - {self.name}"
