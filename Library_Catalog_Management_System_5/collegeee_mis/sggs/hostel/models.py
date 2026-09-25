from django.db import models


class HostelStudent(models.Model):
    regno = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    floor = models.IntegerField()
    fees = models.PositiveSmallIntegerField()
    room_no = models.IntegerField()

    def __str__(self):
        return f"{self.regno} - {self.name}"
