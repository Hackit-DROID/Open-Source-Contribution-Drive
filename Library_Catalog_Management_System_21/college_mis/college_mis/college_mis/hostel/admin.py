from django.contrib import admin
from .models import Hostel

# Optional: create a custom admin display
class HostelAdmin(admin.ModelAdmin):
    list_display = ('student', 'room_no', 'block', 'warden_name')  # columns to display
    search_fields = ('student__name', 'room_no', 'block', 'warden_name')  # search box
    list_filter = ('block', 'warden_name')  # filters in sidebar
    ordering = ('room_no',)  # default ordering

# Register the model with custom admin
admin.site.register(Hostel, HostelAdmin)
