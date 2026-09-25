from django.contrib import admin
from .models import Student, Marks, Attendance


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['reg_no', 'name', 'email', 'branch', 'year', 'gender', 'mobile']
    list_filter = ['branch', 'year', 'gender']
    search_fields = ['reg_no', 'name', 'email']
    ordering = ['name']


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ['student', 'get_overall_percentage']
    search_fields = ['student__name', 'student__reg_no']
    
    def get_overall_percentage(self, obj):
        return f"{obj.get_overall_percentage():.2f}%"
    get_overall_percentage.short_description = 'Overall %'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'attendance_percentage', 'total_classes', 'classes_attended']
    search_fields = ['student__name', 'student__reg_no']
    list_filter = ['attendance_percentage']
