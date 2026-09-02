from django.contrib import admin
from .models import AttendanceRecord, AttendanceSummary

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'course_offering', 'date', 'status', 'marked_by']
    list_filter = ['status', 'date', 'course_offering']
    search_fields = ['student__student_id', 'student__first_name', 'student__last_name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'course_offering', 'total_classes',
        'classes_present', 'classes_absent', 'attendance_percentage'
    ]
    list_filter = ['course_offering']
    search_fields = ['student__student_id', 'student__first_name', 'student__last_name']
    readonly_fields = [
        'total_classes', 'classes_present', 'classes_absent',
        'classes_late', 'classes_excused', 'attendance_percentage', 'updated_at'
    ]
    
    actions = ['update_summaries']
    
    def update_summaries(self, request, queryset):
        for summary in queryset:
            summary.update_summary()
        self.message_user(request, f'{queryset.count()} summaries updated successfully.')
    update_summaries.short_description = 'Update selected summaries'
