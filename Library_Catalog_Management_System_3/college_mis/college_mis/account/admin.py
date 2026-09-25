from django.contrib import admin
from .models import Account

class AccountAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_paid', 'fee_pending', 'last_payment')
    search_fields = ('student__name',)
    list_filter = ('last_payment',)
    ordering = ('student__name',)

admin.site.register(Account, AccountAdmin)
