from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone


def compute_due_date(issue_date=None):
    base = issue_date or timezone.now()
    return base + timedelta(days=settings.LIBRARY_LOAN_DAYS)


def calculate_fine(due_date, return_date=None):
    end = return_date or timezone.now()
    if end <= due_date:
        return Decimal('0.00')
    days_late = (end.date() - due_date.date()).days
    return Decimal(days_late) * Decimal(settings.LIBRARY_FINE_PER_DAY)
