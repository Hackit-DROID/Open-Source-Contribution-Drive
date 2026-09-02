from django.contrib import admin
from .models import Faculty

class FacultyAdmin(admin.ModelAdmin):
    list_display = ['emp_id', 'name', 'department', 'email', 'phone']
    search_fields = ['emp_id', 'name', 'department']
    ordering = ['emp_id']

admin.site.register(Faculty, FacultyAdmin)
