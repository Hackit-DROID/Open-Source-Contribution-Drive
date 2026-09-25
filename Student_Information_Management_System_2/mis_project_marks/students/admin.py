from django.contrib import admin
from .models import Student

# Custom admin for Student
class StudentAdmin(admin.ModelAdmin):
    list_display = ('regno', 'student_name', 'branch', 'phy', 'chem', 'math')  # columns in list view
    search_fields = ('regno', 'student_name', 'branch')                          # search by regno, name, branch
    list_filter = ('branch',)                                                   # filter by branch
    ordering = ('regno',)                                                       # default ordering

# Register Student model with custom admin
admin.site.register(Student, StudentAdmin)
