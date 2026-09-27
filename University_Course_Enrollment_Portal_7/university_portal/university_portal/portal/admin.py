from django.contrib import admin

from .exporters import DATASET_BY_MODEL, build_queryset, select_columns
from .models import Classroom, Course, Department, Instructor, Section, Student, Takes
from .views import build_export_response


class ExportAdminMixin:
    actions = ['export_as_csv', 'export_as_json']

    def _export(self, queryset, fmt):
        dataset = DATASET_BY_MODEL[self.model]
        queryset, _ = build_queryset(dataset, queryset=queryset)
        return build_export_response(dataset, queryset, select_columns(dataset), {}, fmt)

    @admin.action(description='Export selected as CSV')
    def export_as_csv(self, request, queryset):
        return self._export(queryset, 'csv')

    @admin.action(description='Export selected as JSON')
    def export_as_json(self, request, queryset):
        return self._export(queryset, 'json')


@admin.register(Student)
class StudentAdmin(ExportAdminMixin, admin.ModelAdmin):
    list_display = ('ID', 'name', 'dept_name', 'tot_cred')
    list_filter = ('dept_name',)
    search_fields = ('name',)


@admin.register(Instructor)
class InstructorAdmin(ExportAdminMixin, admin.ModelAdmin):
    list_display = ('ID', 'name', 'dept_name', 'salary')
    list_filter = ('dept_name',)
    search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(ExportAdminMixin, admin.ModelAdmin):
    list_display = ('course_id', 'title', 'dept_name', 'credits')
    list_filter = ('dept_name', 'credits')
    search_fields = ('course_id', 'title')


@admin.register(Department)
class DepartmentAdmin(ExportAdminMixin, admin.ModelAdmin):
    list_display = ('dept_name', 'building', 'budget')
    list_filter = ('building',)


@admin.register(Classroom)
class ClassroomAdmin(ExportAdminMixin, admin.ModelAdmin):
    list_display = ('building', 'room_no', 'capacity')
    list_filter = ('building',)


@admin.register(Section)
class SectionAdmin(ExportAdminMixin, admin.ModelAdmin):
    list_display = ('course_id', 'sec_id', 'semester', 'year', 'building', 'room_no', 'time_slot_id')
    list_filter = ('semester', 'year', 'building')
    list_select_related = ('course_id',)


@admin.register(Takes)
class TakesAdmin(ExportAdminMixin, admin.ModelAdmin):
    list_display = ('ID', 'course_id', 'sec_id', 'semester', 'year', 'grade')
    list_filter = ('semester', 'year', 'grade')
    search_fields = ('course_id', 'ID__name')
    list_select_related = ('ID',)
