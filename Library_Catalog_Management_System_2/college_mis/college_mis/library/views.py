
from django.shortcuts import render
from .models import Book

def library_list(request):
    """
    View to list all books in the library.
    """
    books = Book.objects.all()  # fetch all books from DB
    return render(request, 'library/library_list.html', {'books': books})
