

# Register your models here.
from django.contrib import admin
from .models import Account

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('regno', 'fees_type', 'amount')  # Show all columns in admin
