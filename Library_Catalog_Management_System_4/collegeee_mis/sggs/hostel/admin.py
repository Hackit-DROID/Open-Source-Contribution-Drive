from django.contrib import admin
from .models import HostelStudent


@admin.register(HostelStudent)
class HostelStudentAdmin(admin.ModelAdmin):
    list_display = ('regno', 'name', 'floor', 'fees', 'room_no')
    search_fields = ('regno', 'name', 'room_no')
    list_filter = ('name', 'room_no')
    ordering = ('regno',)