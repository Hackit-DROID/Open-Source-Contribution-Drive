from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from users.decorators import librarian_required

from .forms import BookForm
from .models import Book, Category


@login_required
def book_list(request):
    books = Book.objects.all()
    category_slug = request.GET.get('category', '')
    author = request.GET.get('author', '').strip()
    query = request.GET.get('q', '').strip()

    if category_slug:
        books = books.filter(category__slug=category_slug)
    if author:
        books = books.filter(author__icontains=author)
    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(author__icontains=query)
            | Q(description__icontains=query)
            | Q(ai_tags__icontains=query)
        )

    return render(request, 'books/list.html', {
        'books': books,
        'categories': Category.objects.all(),
        'selected_category': category_slug,
        'author_filter': author,
        'query': query,
    })


@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'books/detail.html', {'book': book})


@login_required
def ai_search(request):
    from ai.services import natural_language_search

    query = request.GET.get('q', '').strip()
    results = []
    ai_error = None
    if query:
        try:
            results = natural_language_search(query, Book.objects.all())
        except Exception as exc:
            ai_error = str(exc)
            results = list(Book.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query) | Q(ai_tags__icontains=query)
            ))
    return render(request, 'books/ai_search.html', {
        'query': query,
        'results': results,
        'ai_error': ai_error,
    })


@librarian_required
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f"Book '{book.title}' added. AI summary/tags generated if Gemini is configured.")
            return redirect('books:detail', pk=book.pk)
    else:
        form = BookForm()
    return render(request, 'books/form.html', {'form': form, 'title': 'Add Book'})


@librarian_required
def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, "Book updated.")
            return redirect('books:detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
    return render(request, 'books/form.html', {'form': form, 'title': 'Edit Book', 'book': book})


@librarian_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, "Book deleted.")
        return redirect('books:list')
    return render(request, 'books/confirm_delete.html', {'book': book})
