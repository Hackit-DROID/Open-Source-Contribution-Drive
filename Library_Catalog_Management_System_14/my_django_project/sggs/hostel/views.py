from django.shortcuts import render
from .models import Hostel

def hostel_list(request):
    hostels = Hostel.objects.all()
    return render(request, 'hostel_list.html', {'hostels': hostels})
