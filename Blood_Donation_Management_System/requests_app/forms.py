from django import forms
from .models import BloodRequest
class BloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = ['requester_name','blood_group','units_needed','hospital']
