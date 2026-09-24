import logging
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from account.models import Account, AuditLog
from library.models import Library

logger = logging.getLogger(__name__)

ZERO = Decimal('0.00')


class TransactionError(ValueError):
    pass


def to_amount(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise TransactionError(f"Invalid amount: {value!r}")
    if not amount.is_finite() or amount < 0:
        raise TransactionError(f"Amount must be a non-negative number: {value!r}")
    return amount.quantize(Decimal('0.01'))


def _actor(user):
    if user is not None and getattr(user, 'is_authenticated', False) and user.pk is not None:
        return user
    return None


def record_audit(action, user=None, target=None, detail=None, status=AuditLog.STATUS_SUCCESS):
    actor = _actor(user)
    return AuditLog.objects.create(
        user=actor,
        username=actor.get_username() if actor else '',
        action=action,
        status=status,
        target_model=target._meta.label if target is not None else '',
        target_id=str(target.pk) if target is not None else '',
        detail=detail or {},
    )


@contextmanager
def audited_atomic(action, user=None, detail=None):
    try:
        with transaction.atomic():
            yield
    except Exception as exc:
        failure = dict(detail or {})
        failure['error'] = str(exc)
        failure['error_type'] = type(exc).__name__
        try:
            record_audit(action, user, detail=failure, status=AuditLog.STATUS_FAILED)
        except Exception:
            logger.exception("Could not write failed audit entry for %s", action)
        raise


def _pk(obj):
    return getattr(obj, 'pk', obj)


def _lock_account_for_student(student_id):
    account = (
        Account.objects.select_for_update()
        .filter(student_id=student_id)
        .order_by('pk')
        .first()
    )
    if account is None:
        account = Account.objects.create(student_id=student_id, fees_paid=ZERO, due=ZERO)
    return account


def record_payment(account, amount, user=None):
    amount = to_amount(amount)
    if amount <= ZERO:
        raise TransactionError("Payment amount must be greater than zero.")

    account_id = _pk(account)
    action = 'account.payment'
    with audited_atomic(action, user, {'account_id': account_id, 'amount': amount}):
        try:
            account = Account.objects.select_for_update().get(pk=account_id)
        except Account.DoesNotExist:
            raise TransactionError(f"Account {account_id} does not exist.")
        if amount > account.due:
            raise TransactionError(
                f"Payment of {amount} exceeds outstanding due of {account.due}."
            )

        previous = {'fees_paid': account.fees_paid, 'due': account.due}
        account.fees_paid += amount
        account.due -= amount
        account.save(update_fields=['fees_paid', 'due'])

        record_audit(action, user, account, {
            'amount': amount,
            'student_id': account.student_id,
            'before': previous,
            'after': {'fees_paid': account.fees_paid, 'due': account.due},
        })
    return account


def issue_book(book, student, user=None, fee=0, issued_date=None):
    fee = to_amount(fee)
    book_id = _pk(book)
    student_id = _pk(student)
    action = 'library.issue'
    with audited_atomic(action, user, {'book_id': book_id, 'student_id': student_id, 'fee': fee}):
        try:
            book = Library.objects.select_for_update().get(pk=book_id)
        except Library.DoesNotExist:
            raise TransactionError(f"Book {book_id} does not exist.")
        if book.issued_to_id is not None:
            raise TransactionError(f"Book {book.book_id} is already issued.")

        book.issued_to_id = student_id
        book.issued_date = issued_date or timezone.localdate()
        book.save(update_fields=['issued_to', 'issued_date'])

        account = _lock_account_for_student(student_id)
        previous_due = account.due
        account.due += fee
        account.library = book
        account.save(update_fields=['due', 'library'])

        record_audit(action, user, book, {
            'book_code': book.book_id,
            'student_id': student_id,
            'account_id': account.pk,
            'issued_date': book.issued_date,
            'fee': fee,
            'due': {'before': previous_due, 'after': account.due},
        })
    return book


def return_book(book, user=None, fine=0):
    fine = to_amount(fine)
    book_id = _pk(book)
    action = 'library.return'
    with audited_atomic(action, user, {'book_id': book_id, 'fine': fine}):
        try:
            book = Library.objects.select_for_update().get(pk=book_id)
        except Library.DoesNotExist:
            raise TransactionError(f"Book {book_id} does not exist.")
        if book.issued_to_id is None:
            raise TransactionError(f"Book {book.book_id} is not currently issued.")

        student_id = book.issued_to_id
        issued_date = book.issued_date
        book.issued_to = None
        book.issued_date = None
        book.save(update_fields=['issued_to', 'issued_date'])

        account = _lock_account_for_student(student_id)
        previous_due = account.due
        account.due += fine
        if account.library_id == book.pk:
            account.library = None
        account.save(update_fields=['due', 'library'])

        record_audit(action, user, book, {
            'book_code': book.book_id,
            'student_id': student_id,
            'account_id': account.pk,
            'issued_date': issued_date,
            'fine': fine,
            'due': {'before': previous_due, 'after': account.due},
        })
    return book
