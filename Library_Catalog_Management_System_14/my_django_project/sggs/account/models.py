

# Create your models here.
from django.db import models

class Account(models.Model):
    regno = models.CharField(max_length=20)   # Link to Student's registration no
    fees_type = models.CharField(max_length=50)  # e.g., Tuition, Hostel, Library
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # fees amount

    def __str__(self):
        return f"{self.regno} - {self.fees_type} - {self.amount}"
