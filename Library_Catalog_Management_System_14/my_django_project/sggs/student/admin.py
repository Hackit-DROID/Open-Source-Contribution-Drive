from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('regno', 'name', 'branch', 'year', 'cet')  # show all columns in admin table
