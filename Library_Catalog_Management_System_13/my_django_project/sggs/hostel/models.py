from django.db import models

class Hostel(models.Model):
    hostel_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    warden = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.hostel_id} - {self.name}"
