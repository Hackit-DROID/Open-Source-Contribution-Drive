from django.db import models
from accounts.models import HospitalProfile
class BloodRequest(models.Model):
    requester_name = models.CharField(max_length=200)
    blood_group = models.CharField(max_length=5)
    units_needed = models.PositiveIntegerField(default=1)
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name='requests')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.requester_name} needs {self.units_needed} of {self.blood_group}"
