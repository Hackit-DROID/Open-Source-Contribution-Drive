from django.db import models

class Mess(models.Model):
    student_name = models.CharField(max_length=100)
    meal_type = models.CharField(max_length=20, choices=[('Veg', 'Veg'), ('Non-Veg', 'Non-Veg')])
    month = models.CharField(max_length=20)
    total_days = models.IntegerField()
    attended_days = models.IntegerField()
    charge_per_day = models.DecimalField(max_digits=8, decimal_places=2)

    def total_bill(self):
        return self.attended_days * self.charge_per_day

    def __str__(self):
        return f"{self.student_name} ({self.month})"
