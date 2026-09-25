from django.db import models
from hotel.models import Hotel

class Staff(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)  # common column
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, choices=[
        ('Manager', 'Manager'),
        ('Receptionist', 'Receptionist'),
        ('Housekeeping', 'Housekeeping'),
        ('Chef', 'Chef')
    ])
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.name} ({self.role})"
