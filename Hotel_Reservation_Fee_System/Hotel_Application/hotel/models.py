from django.db import models

class Hotel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=100)
    rating = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.name} ({self.location})"
