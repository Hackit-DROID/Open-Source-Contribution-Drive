from django.db import models
from accounts.models import HospitalProfile
from inventory.models import BloodStock

class Donor(models.Model):
    name = models.CharField(max_length=200)
    blood_group = models.CharField(max_length=5)
    contact = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class Donation(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='donations')
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name='donations')
    blood_sample = models.ForeignKey(BloodStock, on_delete=models.CASCADE, related_name='donations')
    units = models.PositiveIntegerField(default=1)
    donated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Donation {self.id} - {self.donor.name} -> {self.hospital.name}"
