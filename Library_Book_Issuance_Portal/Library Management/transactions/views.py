from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from books.models import Book
from users.decorators import librarian_required, student_required

from .models import IssueRecord


@student_required
@require_POST
def issue_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    with transaction.atomic():
        book.refresh_from_db()
        if book.available_copies <= 0:
            messages.error(request, "Sorry, no copies are currently available.")
            return redirect('books:detail', pk=book.pk)

        already = IssueRecord.objects.filter(
            student=request.user, book=book, status=IssueRecord.STATUS_ISSUED
        ).exists()
        if already:
            messages.warning(request, "You already have this book issued.")
            return redirect('books:detail', pk=book.pk)

        IssueRecord.objects.create(student=request.user, book=book)
        book.available_copies -= 1
        book.save(update_fields=['available_copies'])

    messages.success(request, f"You issued '{book.title}'. Please return it within 14 days.")
    return redirect('transactions:my_books')


@student_required
@require_POST
def return_book(request, issue_id):
    record = get_object_or_404(IssueRecord, pk=issue_id, student=request.user)
    if record.status == IssueRecord.STATUS_RETURNED:
        messages.info(request, "This book is already returned.")
        return redirect('transactions:my_books')

    with transaction.atomic():
        record.return_date = timezone.now()
        record.fine = record.compute_fine()
        record.status = IssueRecord.STATUS_RETURNED
        record.save()

        book = record.book
        book.available_copies += 1
        if book.available_copies > book.total_copies:
            book.available_copies = book.total_copies
        book.save(update_fields=['available_copies'])

    if record.fine > 0:
        messages.warning(request, f"Returned late. Fine owed: Rs. {record.fine}.")
    else:
        messages.success(request, "Book returned on time. Thank you!")
    return redirect('transactions:my_books')


@student_required
def my_books(request):
    records = IssueRecord.objects.filter(student=request.user).select_related('book').order_by('-issue_date')
    active = records.filter(status=IssueRecord.STATUS_ISSUED)
    history = records.filter(status=IssueRecord.STATUS_RETURNED)
    return render(request, 'transactions/my_books.html', {
        'active': active,
        'history': history,
    })


@librarian_required
def all_issues(request):
    status = request.GET.get('status', '')
    records = IssueRecord.objects.select_related('book', 'student').order_by('-issue_date')
    if status in (IssueRecord.STATUS_ISSUED, IssueRecord.STATUS_RETURNED):
        records = records.filter(status=status)
    return render(request, 'transactions/all_issues.html', {
        'records': records,
        'selected_status': status,
    })
