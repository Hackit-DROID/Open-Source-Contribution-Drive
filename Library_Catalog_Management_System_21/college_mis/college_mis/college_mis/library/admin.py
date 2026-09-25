from django.contrib import admin
from .models import Book

class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'copies')  # columns in admin list view
    search_fields = ('title', 'author', 'isbn')            # search box
    list_filter = ('author',)                               # filter sidebar
    ordering = ('title',)                                   # default ordering

admin.site.register(Book, BookAdmin)
