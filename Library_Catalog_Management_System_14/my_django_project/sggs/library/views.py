from django.shortcuts import render, redirect, get_object_or_404
from .models import Library

def library_list(request):
    books = Library.objects.all()
    return render(request, 'library_list.html', {'books': books})

def library_create(request):
    if request.method == 'POST':
        Library.objects.create(
            regno=request.POST.get('regno'),
            book_name=request.POST.get('book_name'),
            date_issue=request.POST.get('date_issue'),
            date_return=request.POST.get('date_return'),
        )
        return redirect('library_list')
    return render(request, 'library_form.html')

def library_update(request, pk):
    book = get_object_or_404(Library, pk=pk)
    if request.method == 'POST':
        book.regno = request.POST.get('regno')
        book.book_name = request.POST.get('book_name')
        book.date_issue = request.POST.get('date_issue')
        book.date_return = request.POST.get('date_return')
        book.save()
        return redirect('library_list')
    return render(request, 'library_form.html', {'book': book})

def library_delete(request, pk):
    book = get_object_or_404(Library, pk=pk)
    if request.method == 'POST':
        book.delete()
        return redirect('library_list')
    return render(request, 'library_confirm_delete.html', {'book': book})


# Create your views here.
