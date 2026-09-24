from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from account.services import TransactionError, issue_book, record_payment, return_book
from library.models import Library
from student.models import Student


class Command(BaseCommand):
    help = 'Run an atomic, audited account or library transaction.'

    def add_arguments(self, parser):
        parser.add_argument('--user', help='Username recorded as the actor in the audit log.')
        subparsers = parser.add_subparsers(dest='operation', required=True)

        payment = subparsers.add_parser('payment', help='Record a fee payment against an account.')
        payment.add_argument('account_id', type=int)
        payment.add_argument('amount')

        issue = subparsers.add_parser('issue', help='Issue a book to a student.')
        issue.add_argument('book_id', help='Book code, e.g. B001.')
        issue.add_argument('roll_no', help='Student roll number.')
        issue.add_argument('--fee', default='0')

        return_parser = subparsers.add_parser('return', help='Return an issued book.')
        return_parser.add_argument('book_id', help='Book code, e.g. B001.')
        return_parser.add_argument('--fine', default='0')

    def handle(self, *args, **options):
        user = self._get_user(options.get('user'))
        operation = options['operation']

        try:
            if operation == 'payment':
                account = record_payment(options['account_id'], options['amount'], user)
                message = f"Recorded payment for {account}. Due is now {account.due}."
            elif operation == 'issue':
                book = issue_book(
                    self._get_book(options['book_id']),
                    self._get_student(options['roll_no']),
                    user,
                    fee=options['fee'],
                )
                message = f"Issued {book} to {book.issued_to}."
            else:
                book = return_book(self._get_book(options['book_id']), user, fine=options['fine'])
                message = f"Returned {book}."
        except TransactionError as exc:
            raise CommandError(f"Transaction rolled back: {exc}")

        self.stdout.write(self.style.SUCCESS(message))

    def _get_user(self, username):
        if not username:
            return None
        User = get_user_model()
        try:
            return User.objects.get(**{User.USERNAME_FIELD: username})
        except User.DoesNotExist:
            raise CommandError(f"Unknown user: {username}")

    def _get_book(self, book_code):
        try:
            return Library.objects.get(book_id=book_code)
        except Library.DoesNotExist:
            raise CommandError(f"Unknown book: {book_code}")

    def _get_student(self, roll_no):
        try:
            return Student.objects.get(roll_no=roll_no)
        except Student.DoesNotExist:
            raise CommandError(f"Unknown student: {roll_no}")
