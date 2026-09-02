

# Create your models here.
from django.db import models

class Hostel(models.Model):
    regno = models.CharField(max_length=20)   # Student's registration number
    hostel_name = models.CharField(max_length=100)
    room_no = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.regno} - {self.hostel_name} - {self.room_no}"
