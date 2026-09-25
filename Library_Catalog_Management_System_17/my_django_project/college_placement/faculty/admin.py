from django.contrib import admin
from .models import Faculty

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'department', 'email', 'phone')
    search_fields = ('name', 'department', 'email')
    list_filter = ('department',)
    list_per_page = 10
