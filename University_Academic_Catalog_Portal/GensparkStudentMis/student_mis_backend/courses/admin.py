from django.contrib import admin
from .models import Course, Instructor, CourseOffering, Enrollment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_name', 'department', 'credits']
    list_filter = ['department', 'credits']
    search_fields = ['course_code', 'course_name']
    filter_horizontal = ['prerequisites']

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ['instructor_id', 'get_full_name', 'department', 'email', 'phone']
    list_filter = ['department']
    search_fields = ['instructor_id', 'first_name', 'last_name', 'email']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'

@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = [
        'course', 'instructor', 'semester', 'year',
        'enrollment_count', 'max_capacity', 'available_seats', 'is_active'
    ]
    list_filter = ['semester', 'year', 'is_active', 'course__department']
    search_fields = ['course__course_code', 'course__course_name', 'instructor__last_name']
    date_hierarchy = 'created_at'
    
    def enrollment_count(self, obj):
        return obj.enrollment_count
    enrollment_count.short_description = 'Enrolled'
    
    def available_seats(self, obj):
        return obj.available_seats
    available_seats.short_description = 'Available'

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'course_offering', 'enrollment_date',
        'status', 'final_grade', 'letter_grade'
    ]
    list_filter = ['status', 'course_offering__semester', 'course_offering__year']
    search_fields = [
        'student__student_id', 'student__first_name', 'student__last_name',
        'course_offering__course__course_code'
    ]
    date_hierarchy = 'enrollment_date'
    readonly_fields = ['enrollment_date', 'created_at', 'updated_at']
