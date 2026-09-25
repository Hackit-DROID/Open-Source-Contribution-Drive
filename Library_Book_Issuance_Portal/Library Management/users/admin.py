from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'roll_number', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Library info', {'fields': ('role', 'phone', 'roll_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Library info', {'fields': ('role', 'phone', 'roll_number')}),
    )
