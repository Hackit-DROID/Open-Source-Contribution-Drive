from django.db import models
from hotel.models import Hotel
from booking.models import Booking

class Payment(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)  # common column
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=[
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('UPI', 'UPI')
    ], default='Cash')

    def __str__(self):
        return f"Payment {self.id} - {self.booking.guest.name}"
