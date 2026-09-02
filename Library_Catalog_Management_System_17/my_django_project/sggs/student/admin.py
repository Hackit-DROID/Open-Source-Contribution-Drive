# student/admin.py
from django.contrib import admin
from .models import Student

class StudentAdmin(admin.ModelAdmin):   # ✅ Capitalized name
    list_display = ['regno', 'name', 'branch', 'year']
    search_fields = ['regno', 'name', 'branch', 'year']
    ordering = ("id",)                  # ✅ spelling fixed (was 'oredring')
    list_per_page = 5

admin.site.register(Student, StudentAdmin)   # ✅ matches class name
