from django.contrib import admin
from .models import Department, Student

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'student_count', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['created_at']
    
    def student_count(self, obj):
        return obj.students.filter(status='active').count()
    student_count.short_description = 'Active Students'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'student_id', 'get_full_name', 'email', 'department',
        'year', 'status', 'enrollment_date'
    ]
    list_filter = ['department', 'year', 'status', 'gender']
    search_fields = ['student_id', 'first_name', 'last_name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'enrollment_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student_id', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Academic Information', {
            'fields': ('department', 'year', 'enrollment_date', 'status')
        }),
        ('Personal Information', {
            'fields': (
                'date_of_birth', 'gender', 'address', 'city',
                'state', 'country', 'postal_code'
            )
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone',
                'emergency_contact_relation'
            ),
            'classes': ('collapse',)
        }),
        ('Profile', {
            'fields': ('profile_picture',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
