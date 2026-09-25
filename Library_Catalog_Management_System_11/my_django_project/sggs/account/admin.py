from django.contrib import admin
from .models import Account

class AccountAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'student_roll_no', 'fees_paid', 'due')  # display related student info
    ordering = ('student__roll_no',)
    search_fields = ('student__name', 'student__roll_no')  # search by student name or roll no

    # Method to display student name
    def student_name(self, obj):
        return obj.student.name
    student_name.short_description = 'Student Name'

    # Method to display student roll number
    def student_roll_no(self, obj):
        return obj.student.roll_no
    student_roll_no.short_description = 'Reg. No'

admin.site.register(Account, AccountAdmin)
