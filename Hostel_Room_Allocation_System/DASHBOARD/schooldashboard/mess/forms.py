from django import forms
from .models import Mess

class MessForm(forms.ModelForm):
    class Meta:
        model = Mess
        fields = '__all__'
