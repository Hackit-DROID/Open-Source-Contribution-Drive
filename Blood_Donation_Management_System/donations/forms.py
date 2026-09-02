from django import forms
from .models import Donor, Donation
class DonorForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = ['name','blood_group','contact','city']

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['donor','blood_sample','units']
