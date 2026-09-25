from django.contrib import admin
from .models import Library

@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('regno', 'book_name', 'date_issue', 'date_return')
    search_fields = ['regno', 'book_name']
    ordering = ("id",)
    list_per_page = 5
