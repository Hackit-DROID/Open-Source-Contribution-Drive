from django import forms
from .models import Hostel


class HostelForm(forms.ModelForm):
    class Meta:
        model = Hostel
        fields = ['student_name', 'room_no', 'block', 'floor', 'warden_name', 'rent', 'status']
        widgets = {
            'student_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-gray-900',
                'placeholder': 'Enter student full name (or "Vacant / Unallocated")',
            }),
            'room_no': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-gray-900',
                'placeholder': 'e.g. 101, B-204',
            }),
            'block': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-gray-900',
                'placeholder': 'e.g. Block A, Wing 1',
            }),
            'floor': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-gray-900',
                'placeholder': 'e.g. 1, 2, 3',
                'min': '0',
            }),
            'warden_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-gray-900',
                'placeholder': 'Supervising warden name',
            }),
            'rent': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-gray-900',
                'placeholder': 'e.g. 4500.00',
                'step': '0.01',
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition text-gray-900 bg-white',
            }),
        }

    def clean_rent(self):
        rent = self.cleaned_data.get('rent')
        if rent is not None and rent < 0:
            raise forms.ValidationError("Rent amount cannot be negative.")
        return rent
