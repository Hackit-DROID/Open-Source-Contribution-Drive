from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, date, time
from .models import Room, Booking
from .conference_pricing import (
    ConferenceHallPricingEngine,
    ConferenceHall,
    ConferenceBooking,
    DEFAULT_CATERING_RATE_PER_HEAD,
)

def room_list(request):
    rooms = Room.objects.all()
    return render(request, "room_list.html", {"rooms": rooms})

def booking_list(request):
    bookings = Booking.objects.all()
    return render(request, "booking_list.html", {"bookings": bookings})


def conference_event_pricing_view(request):
    """API endpoint to compute conference hall event pricing package and check availability."""
    try:
        hall_rate = float(request.GET.get('hall_rate', 1000.0))
        attendee_count = int(request.GET.get('attendee_count', 50))
        catering_rate = float(request.GET.get('catering_rate', DEFAULT_CATERING_RATE_PER_HEAD))
        equipment_fee = float(request.GET.get('equipment_fee', 250.0))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid pricing parameters provided."}, status=400)

    engine = ConferenceHallPricingEngine(default_catering_rate=DEFAULT_CATERING_RATE_PER_HEAD)
    cost_summary = engine.calculate_event_cost(
        hall_rate=hall_rate,
        attendee_count=attendee_count,
        catering_rate=catering_rate,
        equipment_fee=equipment_fee,
    )

    return JsonResponse({
        "status": "success",
        "pricing_breakdown": cost_summary,
        "parameters": {
            "hall_rate": hall_rate,
            "attendee_count": attendee_count,
            "catering_rate": catering_rate,
            "equipment_fee": equipment_fee,
        },
    })
