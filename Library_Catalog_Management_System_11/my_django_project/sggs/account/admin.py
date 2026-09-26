from django.contrib import admin, messages
from .models import Account, AuditLog
from .services import TransactionError, record_payment

class AccountAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'student_roll_no', 'fees_paid', 'due')  # display related student info
    ordering = ('student__roll_no',)
    search_fields = ('student__name', 'student__roll_no')  # search by student name or roll no
    actions = ['settle_dues']

    # Method to display student name
    def student_name(self, obj):
        return obj.student.name
    student_name.short_description = 'Student Name'

    # Method to display student roll number
    def student_roll_no(self, obj):
        return obj.student.roll_no
    student_roll_no.short_description = 'Reg. No'

    @admin.action(description='Settle outstanding dues for selected accounts')
    def settle_dues(self, request, queryset):
        settled = failed = 0
        for account in queryset.filter(due__gt=0):
            try:
                record_payment(account, account.due, request.user)
                settled += 1
            except TransactionError as exc:
                failed += 1
                self.message_user(request, f"{account}: {exc}", messages.ERROR)

        self.message_user(request, f"Settled dues for {settled} account(s).", messages.SUCCESS)
        if failed:
            self.message_user(request, f"{failed} account(s) were rolled back.", messages.WARNING)

admin.site.register(Account, AccountAdmin)


class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'status', 'username', 'target_model', 'target_id')
    list_filter = ('action', 'status')
    search_fields = ('username', 'action', 'target_id')
    date_hierarchy = 'created_at'
    readonly_fields = [field.name for field in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(AuditLog, AuditLogAdmin)
