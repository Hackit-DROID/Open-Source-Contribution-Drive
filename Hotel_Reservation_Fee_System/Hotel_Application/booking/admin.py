from django.contrib import admin
from .models import Room, Booking

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'hotel', 'room_type', 'price_per_night', 'is_available')
    search_fields = ('room_number', 'room_type')
    list_filter = ('hotel', 'room_type', 'is_available')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('guest', 'hotel', 'room', 'check_in', 'check_out', 'status')
    search_fields = ('guest__name', 'room__room_number')
    list_filter = ('hotel', 'status', 'check_in', 'check_out')
