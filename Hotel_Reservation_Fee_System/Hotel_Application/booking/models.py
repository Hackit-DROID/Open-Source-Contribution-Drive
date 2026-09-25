from django.db import models
from hotel.models import Hotel
from guest.models import Guest

class Room(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)  # common column
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=20, choices=[
        ('Single', 'Single'),
        ('Double', 'Double'),
        ('Suite', 'Suite')
    ])
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.room_number} ({self.room_type})"


class Booking(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)  # common column
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('Booked', 'Booked'),
        ('Checked-In', 'Checked-In'),
        ('Checked-Out', 'Checked-Out')
    ], default='Booked')

    def __str__(self):
        return f"{self.guest.name} - {self.room.room_number}"
