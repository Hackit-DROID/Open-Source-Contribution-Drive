from django.contrib import admin
from .models import Hostel

class HostelAdmin(admin.ModelAdmin):
    list_display = ['hostel_id', 'name', 'warden', 'capacity']
    search_fields = ['hostel_id', 'name', 'warden']
    ordering = ['hostel_id']

admin.site.register(Hostel, HostelAdmin)
