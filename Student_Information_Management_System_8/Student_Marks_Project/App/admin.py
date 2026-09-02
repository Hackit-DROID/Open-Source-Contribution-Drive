from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("reg_no", "student_name", "branch", "math", "phy", "chem")
    search_fields = ("student_name", "reg_no", "branch")
    list_filter = ("branch",)
