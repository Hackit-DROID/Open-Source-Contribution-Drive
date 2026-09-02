from django import forms
from .models import BloodStock
class BloodStockForm(forms.ModelForm):
    class Meta:
        model = BloodStock
        fields = ['blood_sample_id','blood_group','units','hospital']
