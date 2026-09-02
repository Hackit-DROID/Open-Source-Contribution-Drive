from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('regno', 'student_name', 'branch', 'phy', 'chem', 'math')

    search_fields = ['student_name']

    list_filter = ['branch']