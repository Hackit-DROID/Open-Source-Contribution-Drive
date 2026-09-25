from django.contrib import admin
from .models import Guest

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel', 'email', 'phone')
    search_fields = ('name', 'email')
    list_filter = ('hotel',)
