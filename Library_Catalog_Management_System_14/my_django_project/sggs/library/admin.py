

# Register your models here.
from django.contrib import admin
from .models import Library

@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('regno', 'book_name', 'date_issue', 'date_return')  # Show all columns
