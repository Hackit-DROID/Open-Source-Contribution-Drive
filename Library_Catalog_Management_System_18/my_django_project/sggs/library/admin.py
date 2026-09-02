from django.contrib import admin
from .models import Library

class LibraryAdmin(admin.ModelAdmin):
    list_display = ['book_id', 'title', 'author', 'issued_to', 'issued_date']
    search_fields = ['book_id', 'title', 'author']
    ordering = ['book_id']

admin.site.register(Library, LibraryAdmin)
