from django.db import models
from student.models import Student  # Assuming student app exists

class Account(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    fee_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fee_pending = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_payment = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - Paid: {self.fee_paid}"
