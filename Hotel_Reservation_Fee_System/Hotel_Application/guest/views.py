from django.shortcuts import render
from .models import Guest

def guest_list(request):
    guests = Guest.objects.all()   # fetch all guests
    return render(request, "guest_list.html", {"guests": guests})

