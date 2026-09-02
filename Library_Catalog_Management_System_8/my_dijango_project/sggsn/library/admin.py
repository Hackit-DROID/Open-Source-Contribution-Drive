from django.contrib import admin
from .models import Library

@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('student', 'regno', 'book_title', 'issue_date', 'return_date', 'fine')

