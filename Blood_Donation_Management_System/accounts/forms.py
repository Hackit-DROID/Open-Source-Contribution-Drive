from django import forms
from .models import HospitalProfile
class HospitalForm(forms.ModelForm):
    class Meta:
        model = HospitalProfile
        fields = ['user','name','address']
