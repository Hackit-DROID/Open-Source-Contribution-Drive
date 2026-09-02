from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'regno', 'email', 'department')  # fields you want to see
    search_fields = ['name', 'regno', 'email']
    list_per_page = 10
