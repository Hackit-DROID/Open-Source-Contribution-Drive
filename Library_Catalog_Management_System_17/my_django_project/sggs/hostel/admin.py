from django.contrib import admin
from .models import Hostel

class HostelAdmin(admin.ModelAdmin):
    list_display = ['regno', 'hostel_name', 'room_no']
    search_fields = ['regno', 'hostel_name', 'room_no']
    ordering = ("id",)
    list_per_page = 3

admin.site.register(Hostel, HostelAdmin)
