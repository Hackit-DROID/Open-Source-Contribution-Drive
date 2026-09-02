from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('regno', 'name', 'branch', 'year', 'cet')   # Show all columns
    search_fields = ('regno', 'name', 'branch')                 # Search option
    list_filter = ('branch', 'year')                            # Filter sidebar
    ordering = ('regno',)                                       # Default ordering