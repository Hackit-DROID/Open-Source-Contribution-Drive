from django.contrib import admin

from .models import Book, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'total_copies', 'available_copies', 'added_on')
    list_filter = ('category',)
    search_fields = ('title', 'author', 'isbn', 'ai_tags')
    readonly_fields = ('ai_summary', 'ai_tags', 'added_on')
