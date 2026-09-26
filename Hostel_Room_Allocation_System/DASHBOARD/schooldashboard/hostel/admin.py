from django.contrib import admin
from .models import Hostel


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'room_no', 'block', 'floor', 'warden_name', 'rent', 'status')
    list_filter = ('status', 'block', 'floor')
    search_fields = ('student_name', 'room_no', 'warden_name', 'block')
    list_editable = ('status', 'rent')
    ordering = ('block', 'floor', 'room_no')
