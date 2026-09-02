from django.contrib import admin
from .models import Account   # ✅ Capitalized

class AccountAdmin(admin.ModelAdmin):
    list_display = ['regno', 'fees_type', 'amount']
    search_fields = ['regno', 'fees_type', 'amount']
    ordering = ("id",)   # ✅ fixed typo

    list_per_page = 3

admin.site.register(Account, AccountAdmin)
