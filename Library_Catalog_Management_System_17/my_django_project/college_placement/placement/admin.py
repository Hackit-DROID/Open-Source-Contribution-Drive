from django.contrib import admin
from .models import Placement

@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'company', 'role', 'package', 'date_selected')
    search_fields = ('student__name', 'company__name', 'role')
    list_filter = ('company', 'date_selected')
    list_per_page = 10
