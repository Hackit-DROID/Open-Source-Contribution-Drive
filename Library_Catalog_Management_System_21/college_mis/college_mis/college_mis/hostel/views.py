from django.shortcuts import render
from .models import Hostel  # Make sure Hostel model exists in models.py

def hostel_list(request):
    hostels = Hostel.objects.all()
    return render(request, 'hostel/hostel_list.html', {'hostels': hostels})
