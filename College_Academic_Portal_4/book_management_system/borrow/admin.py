from django.contrib import admin
from .models import BorrowRecord

@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'borrower', 'book', 'borrowed_at', 'due_date', 'returned')
    list_filter = ('returned', 'due_date')
    search_fields = ('borrower__name', 'book__title')
