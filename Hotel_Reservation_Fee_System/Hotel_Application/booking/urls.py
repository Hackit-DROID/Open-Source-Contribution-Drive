from django.urls import path
from . import views

urlpatterns = [
    path("rooms/", views.room_list, name="room_list"),
    path("bookings/", views.booking_list, name="booking_list"),
]
