from django.shortcuts import render
from .models import Hotel

def hotel_list(request):
    hotels = Hotel.objects.all()
    return render(request, "hotel_list.html", {"hotels": hotels})
