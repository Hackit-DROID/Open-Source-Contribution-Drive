from django.contrib import admin
from .models import Staff

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel', 'role', 'email', 'phone')
    search_fields = ('name', 'email', 'role')
    list_filter = ('hotel', 'role')
