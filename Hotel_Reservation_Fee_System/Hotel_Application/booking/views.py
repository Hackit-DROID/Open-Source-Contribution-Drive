from django.shortcuts import render
from .models import Room, Booking

def room_list(request):
    rooms = Room.objects.all()
    return render(request, "room_list.html", {"rooms": rooms})

def booking_list(request):
    bookings = Booking.objects.all()
    return render(request, "booking_list.html", {"bookings": bookings})
