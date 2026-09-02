from django.contrib import admin

from .models import Account

class AccountAdmin(admin.ModelAdmin):
    # show all columns
    list_display = ['student','regno','hostel_fees','library_fees','exam_fees','total_fees' ]

    search_fields = [ 'student','regno','hostel_fees','library_fees','exam_fees','total_fees']

    ordering = ("id",)
    list_per_page = 25

admin.site.register(Account, AccountAdmin)

# Register your models here.
