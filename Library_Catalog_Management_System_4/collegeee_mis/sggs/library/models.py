from django.db import models


class LibraryStudent(models.Model):
    regno = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    branch = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()
    books = models.FloatField()

    def __str__(self):
        return f"{self.regno} - {self.name}"