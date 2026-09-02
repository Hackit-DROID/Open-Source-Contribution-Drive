

# Register your models here.
from django.contrib import admin
from .models import Hostel

@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('regno', 'hostel_name', 'room_no')  # Show all columns
