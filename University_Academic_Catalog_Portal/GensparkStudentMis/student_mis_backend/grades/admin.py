from django.contrib import admin
from .models import AssessmentType, Assessment, Grade, GradeReport

@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'weight_percentage', 'created_at']
    search_fields = ['name']

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'course_offering', 'assessment_type',
        'max_score', 'weight_percentage', 'due_date', 'is_published'
    ]
    list_filter = ['assessment_type', 'is_published', 'course_offering__semester', 'course_offering__year']
    search_fields = ['title', 'course_offering__course__course_code']
    date_hierarchy = 'due_date'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'assessment', 'score', 'percentage',
        'weighted_score', 'graded_date', 'is_late'
    ]
    list_filter = ['assessment__assessment_type', 'is_late', 'graded_date']
    search_fields = [
        'student__student_id', 'student__first_name', 'student__last_name',
        'assessment__title'
    ]
    date_hierarchy = 'graded_date'
    readonly_fields = ['graded_date', 'created_at', 'updated_at', 'percentage', 'weighted_score']

@admin.register(GradeReport)
class GradeReportAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'enrollment', 'percentage', 'letter_grade',
        'gpa', 'is_finalized', 'finalized_date'
    ]
    list_filter = ['letter_grade', 'is_finalized', 'enrollment__course_offering__semester']
    search_fields = [
        'student__student_id', 'student__first_name', 'student__last_name',
        'enrollment__course_offering__course__course_code'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['calculate_grades', 'finalize_grades']
    
    def calculate_grades(self, request, queryset):
        for report in queryset:
            report.calculate_final_grade()
        self.message_user(request, f'{queryset.count()} grades calculated successfully.')
    calculate_grades.short_description = 'Calculate final grades'
    
    def finalize_grades(self, request, queryset):
        from datetime import date
        for report in queryset:
            report.calculate_final_grade()
            report.is_finalized = True
            report.finalized_date = date.today()
            report.save()
        self.message_user(request, f'{queryset.count()} grades finalized successfully.')
    finalize_grades.short_description = 'Finalize grades'
