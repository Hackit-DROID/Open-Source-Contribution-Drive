from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    roll_number = forms.CharField(max_length=32, required=True, label='Roll Number')
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'roll_number', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_STUDENT
        user.email = self.cleaned_data['email']
        user.roll_number = self.cleaned_data['roll_number']
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user
