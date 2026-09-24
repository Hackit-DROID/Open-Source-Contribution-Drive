from django.contrib import admin

from .models import IssueRecord


@admin.register(IssueRecord)
class IssueRecordAdmin(admin.ModelAdmin):
    list_display = ('book', 'student', 'issue_date', 'due_date', 'return_date', 'status', 'fine')
    list_filter = ('status',)
    search_fields = ('book__title', 'student__username')
    readonly_fields = ('issue_date',)
