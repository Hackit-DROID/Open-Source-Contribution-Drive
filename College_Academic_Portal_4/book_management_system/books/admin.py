from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'isbn', 'available_copies', 'added_by', 'created_at')
    search_fields = ('title', 'author', 'isbn')
    list_filter = ('author',)
