from django.db import models
from accounts.models import HospitalProfile

class BloodStock(models.Model):
    blood_sample_id = models.CharField(max_length=50, primary_key=True)
    blood_group = models.CharField(max_length=5)
    units = models.PositiveIntegerField(default=0)
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name='stocks')

    def __str__(self):
        return f"{self.blood_sample_id} - {self.blood_group} ({self.units})"
