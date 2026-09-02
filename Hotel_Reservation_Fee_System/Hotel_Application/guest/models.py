from django.db import models
from hotel.models import Hotel

class Guest(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)  # common column
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()

    def __str__(self):
        return self.name
