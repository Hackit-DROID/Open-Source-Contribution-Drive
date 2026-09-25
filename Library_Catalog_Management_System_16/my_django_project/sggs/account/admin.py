from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from account.notifications import notify_user

User = get_user_model()


class NotificationUserAdmin(UserAdmin):
    actions = ['send_account_status_email']

    @admin.action(description='Send account status email to selected users')
    def send_account_status_email(self, request, queryset):
        sent = skipped = failed = 0
        for user in queryset:
            if not user.email:
                skipped += 1
                continue
            status = 'active' if user.is_active else 'deactivated'
            if notify_user(user, 'account_status', {'status': status}):
                sent += 1
            else:
                failed += 1

        self.message_user(request, 'Sent %d account status email(s).' % sent, messages.SUCCESS)
        if skipped:
            self.message_user(request, 'Skipped %d user(s) without an email address.' % skipped, messages.WARNING)
        if failed:
            self.message_user(request, 'Failed to send %d email(s). Check the logs.' % failed, messages.ERROR)


if admin.site.is_registered(User):
    admin.site.unregister(User)
admin.site.register(User, NotificationUserAdmin)
