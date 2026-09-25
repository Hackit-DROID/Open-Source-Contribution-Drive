from django.contrib import admin
from .models import LibraryStudent


@admin.register(LibraryStudent)
class LibraryStudentAdmin(admin.ModelAdmin):
    list_display = ('regno', 'name', 'branch', 'year', 'books')
    search_fields = ('regno', 'name', 'branch')
    list_filter = ('branch', 'year')
    ordering = ('regno',)