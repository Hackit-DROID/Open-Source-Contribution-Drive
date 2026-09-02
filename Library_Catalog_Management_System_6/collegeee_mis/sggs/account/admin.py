from django.contrib import admin
from .models import AccountStudent


@admin.register(AccountStudent)
class AccountStudentAdmin(admin.ModelAdmin):
    list_display = ('regno', 'name', 'branch', 'acc_id', 'fees')
    search_fields = ('regno', 'name', 'branch')
    list_filter = ('branch', 'acc_id')
    ordering = ('regno',)