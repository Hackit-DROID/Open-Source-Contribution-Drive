from django.db import models

# Create your models here.


class Account(models.Model):
    student = models.CharField(max_length=100)          # Student name
    regno = models.CharField(max_length=20, unique=True) # Registration number
    hostel_fees = models.DecimalField(max_digits=8, decimal_places=2)  # Hostel fee
    library_fees = models.DecimalField(max_digits=8, decimal_places=2) # Library fee
    exam_fees = models.DecimalField(max_digits=8, decimal_places=2)    # Exam fee
    total_fees = models.DecimalField(max_digits=10, decimal_places=2)  # Total

    def __str__(self):
        return f"{self.regno} - {self.student}"
