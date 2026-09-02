from django.contrib import admin
from .models import Student

class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'roll_no', 'branch', 'physics', 'chemistry', 'maths')
    search_fields = ('name', 'roll_no')   # Search by name or roll no
    list_filter = ('branch',)             # Filter by branch dropdown
    ordering = ('roll_no',)

admin.site.register(Student, StudentAdmin)
