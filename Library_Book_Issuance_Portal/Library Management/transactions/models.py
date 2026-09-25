from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from books.models import Book

from .utils import calculate_fine, compute_due_date


class IssueRecord(models.Model):
    STATUS_ISSUED = 'issued'
    STATUS_RETURNED = 'returned'
    STATUS_CHOICES = [
        (STATUS_ISSUED, 'Issued'),
        (STATUS_RETURNED, 'Returned'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='issues')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issues')

    issue_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(null=True, blank=True)

    fine = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ISSUED)

    class Meta:
        ordering = ['-issue_date']

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = compute_due_date(self.issue_date)
        super().save(*args, **kwargs)

    def compute_fine(self):
        return calculate_fine(self.due_date, self.return_date)

    @property
    def is_overdue(self):
        return self.status == self.STATUS_ISSUED and timezone.now() > self.due_date

    def __str__(self):
        return f"{self.book.title} -> {self.student.username} ({self.status})"
