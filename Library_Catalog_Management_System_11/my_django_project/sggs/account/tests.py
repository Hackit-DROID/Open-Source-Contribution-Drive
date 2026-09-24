from datetime import date
from decimal import Decimal
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse

from account import services
from account.models import Account, AuditLog, ImmutableAuditLogError
from account.services import TransactionError, issue_book, record_payment, return_book
from library.models import Library
from student.models import Student

User = get_user_model()


class TransactionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('librarian', password='pass')
        self.student = Student.objects.create(name='Asha', roll_no='R001')
        self.account = Account.objects.create(
            student=self.student, fees_paid=Decimal('100.00'), due=Decimal('500.00')
        )
        self.book = Library.objects.create(book_id='B001', title='Clean Code', author='Robert Martin')

    def reload(self):
        self.account.refresh_from_db()
        self.book.refresh_from_db()


class RecordPaymentTests(TransactionTestCase):
    def test_updates_balances_and_writes_audit_entry(self):
        record_payment(self.account, '150.50', self.user)

        self.reload()
        self.assertEqual(self.account.fees_paid, Decimal('250.50'))
        self.assertEqual(self.account.due, Decimal('349.50'))

        log = AuditLog.objects.get()
        self.assertEqual(log.action, 'account.payment')
        self.assertEqual(log.status, AuditLog.STATUS_SUCCESS)
        self.assertEqual(log.user_id, self.user.pk)
        self.assertEqual(log.username, 'librarian')
        self.assertEqual(log.target_model, 'account.Account')
        self.assertEqual(log.target_id, str(self.account.pk))
        self.assertIsNotNone(log.created_at)
        self.assertEqual(log.detail['amount'], '150.50')
        self.assertEqual(log.detail['before'], {'fees_paid': '100.00', 'due': '500.00'})
        self.assertEqual(log.detail['after'], {'fees_paid': '250.50', 'due': '349.50'})

    def test_accepts_account_id(self):
        record_payment(self.account.pk, 100, self.user)

        self.reload()
        self.assertEqual(self.account.due, Decimal('400.00'))

    def test_overpayment_is_rolled_back_and_audited_as_failure(self):
        with self.assertRaises(TransactionError):
            record_payment(self.account, '600', self.user)

        self.reload()
        self.assertEqual(self.account.fees_paid, Decimal('100.00'))
        self.assertEqual(self.account.due, Decimal('500.00'))

        log = AuditLog.objects.get()
        self.assertEqual(log.status, AuditLog.STATUS_FAILED)
        self.assertEqual(log.user_id, self.user.pk)
        self.assertEqual(log.detail['error_type'], 'TransactionError')
        self.assertIn('exceeds outstanding due', log.detail['error'])

    def test_audit_write_failure_rolls_back_balance_update(self):
        original = services.record_audit

        def failing_success_audit(*args, **kwargs):
            if kwargs.get('status', AuditLog.STATUS_SUCCESS) == AuditLog.STATUS_SUCCESS:
                raise RuntimeError('audit store unavailable')
            return original(*args, **kwargs)

        with mock.patch.object(services, 'record_audit', side_effect=failing_success_audit):
            with self.assertRaises(RuntimeError):
                record_payment(self.account, '100', self.user)

        self.reload()
        self.assertEqual(self.account.fees_paid, Decimal('100.00'))
        self.assertEqual(self.account.due, Decimal('500.00'))
        self.assertEqual(AuditLog.objects.get().status, AuditLog.STATUS_FAILED)

    def test_invalid_amounts_are_rejected(self):
        for amount in ('0', '-5', 'abc', None, 'NaN'):
            with self.subTest(amount=amount), self.assertRaises(TransactionError):
                record_payment(self.account, amount, self.user)

        self.reload()
        self.assertEqual(self.account.due, Decimal('500.00'))

    def test_missing_account_is_rolled_back(self):
        with self.assertRaises(TransactionError):
            record_payment(9999, '10', self.user)
        self.assertEqual(AuditLog.objects.get().status, AuditLog.STATUS_FAILED)

    def test_anonymous_user_is_recorded_without_actor(self):
        record_payment(self.account, '10', AnonymousUser())

        log = AuditLog.objects.get()
        self.assertIsNone(log.user)
        self.assertEqual(log.username, '')


class IssueAndReturnBookTests(TransactionTestCase):
    def test_issue_updates_book_and_account_atomically(self):
        issue_book(self.book, self.student, self.user, fee='20', issued_date=date(2026, 9, 1))

        self.reload()
        self.assertEqual(self.book.issued_to, self.student)
        self.assertEqual(self.book.issued_date, date(2026, 9, 1))
        self.assertEqual(self.account.due, Decimal('520.00'))
        self.assertEqual(self.account.library, self.book)

        log = AuditLog.objects.get()
        self.assertEqual(log.action, 'library.issue')
        self.assertEqual(log.target_model, 'library.Library')
        self.assertEqual(log.target_id, str(self.book.pk))
        self.assertEqual(log.detail['due'], {'before': '500.00', 'after': '520.00'})

    def test_issue_creates_account_when_missing(self):
        other = Student.objects.create(name='Ravi', roll_no='R002')

        issue_book(self.book, other, self.user)

        self.assertTrue(Account.objects.filter(student=other, library=self.book).exists())

    def test_issue_rolls_back_book_when_account_update_fails(self):
        with mock.patch.object(Account, 'save', side_effect=RuntimeError('disk full')):
            with self.assertRaises(RuntimeError):
                issue_book(self.book, self.student, self.user, fee='20')

        self.reload()
        self.assertIsNone(self.book.issued_to)
        self.assertIsNone(self.book.issued_date)
        self.assertEqual(self.account.due, Decimal('500.00'))

        log = AuditLog.objects.get()
        self.assertEqual(log.status, AuditLog.STATUS_FAILED)
        self.assertEqual(log.detail['error'], 'disk full')
        self.assertEqual(log.detail['book_id'], self.book.pk)

    def test_issuing_already_issued_book_fails(self):
        issue_book(self.book, self.student, self.user)
        other = Student.objects.create(name='Ravi', roll_no='R002')

        with self.assertRaises(TransactionError):
            issue_book(self.book, other, self.user)

        self.reload()
        self.assertEqual(self.book.issued_to, self.student)
        self.assertEqual(AuditLog.objects.filter(status=AuditLog.STATUS_FAILED).count(), 1)

    def test_return_clears_issue_and_applies_fine(self):
        issue_book(self.book, self.student, self.user, issued_date=date(2026, 9, 1))

        return_book(self.book, self.user, fine='15.25')

        self.reload()
        self.assertIsNone(self.book.issued_to)
        self.assertIsNone(self.book.issued_date)
        self.assertIsNone(self.account.library)
        self.assertEqual(self.account.due, Decimal('515.25'))

        log = AuditLog.objects.filter(action='library.return').get()
        self.assertEqual(log.detail['student_id'], self.student.pk)
        self.assertEqual(log.detail['issued_date'], '2026-09-01')
        self.assertEqual(log.detail['fine'], '15.25')

    def test_return_rolls_back_when_account_update_fails(self):
        issue_book(self.book, self.student, self.user)

        with mock.patch.object(Account, 'save', side_effect=RuntimeError('boom')):
            with self.assertRaises(RuntimeError):
                return_book(self.book, self.user, fine='10')

        self.reload()
        self.assertEqual(self.book.issued_to, self.student)
        self.assertEqual(self.account.due, Decimal('500.00'))

    def test_returning_book_that_is_not_issued_fails(self):
        with self.assertRaises(TransactionError):
            return_book(self.book, self.user)
        self.assertEqual(AuditLog.objects.get().status, AuditLog.STATUS_FAILED)


class AuditLogImmutabilityTests(TransactionTestCase):
    def setUp(self):
        super().setUp()
        record_payment(self.account, '10', self.user)
        self.log = AuditLog.objects.get()

    def test_entry_cannot_be_modified(self):
        self.log.action = 'tampered'
        with self.assertRaises(ImmutableAuditLogError):
            self.log.save()

    def test_entry_cannot_be_deleted(self):
        with self.assertRaises(ImmutableAuditLogError):
            self.log.delete()

    def test_queryset_update_and_delete_are_blocked(self):
        with self.assertRaises(ImmutableAuditLogError):
            AuditLog.objects.update(action='tampered')
        with self.assertRaises(ImmutableAuditLogError):
            AuditLog.objects.all().delete()
        self.assertEqual(AuditLog.objects.get().action, 'account.payment')

    def test_deleting_user_keeps_audit_history(self):
        self.user.delete()

        log = AuditLog.objects.get()
        self.assertIsNone(log.user)
        self.assertEqual(log.username, 'librarian')


class AccountTransactionCommandTests(TransactionTestCase):
    def call(self, *args):
        out = StringIO()
        call_command('account_transaction', *args, stdout=out)
        return out.getvalue()

    def test_payment_command(self):
        output = self.call('--user', 'librarian', 'payment', str(self.account.pk), '200')

        self.reload()
        self.assertEqual(self.account.due, Decimal('300.00'))
        self.assertIn('Due is now 300.00', output)
        self.assertEqual(AuditLog.objects.get().username, 'librarian')

    def test_issue_and_return_commands(self):
        self.call('--user', 'librarian', 'issue', 'B001', 'R001', '--fee', '5')
        self.reload()
        self.assertEqual(self.book.issued_to, self.student)

        self.call('--user', 'librarian', 'return', 'B001', '--fine', '2.50')
        self.reload()
        self.assertIsNone(self.book.issued_to)
        self.assertEqual(self.account.due, Decimal('507.50'))
        self.assertEqual(AuditLog.objects.count(), 2)

    def test_failed_command_reports_rollback(self):
        with self.assertRaisesMessage(CommandError, 'Transaction rolled back'):
            self.call('payment', str(self.account.pk), '9999')

        self.reload()
        self.assertEqual(self.account.due, Decimal('500.00'))
        self.assertEqual(AuditLog.objects.get().status, AuditLog.STATUS_FAILED)

    def test_unknown_references_raise_command_error(self):
        for args in (
            ('--user', 'ghost', 'payment', str(self.account.pk), '1'),
            ('issue', 'NOPE', 'R001'),
            ('issue', 'B001', 'NOPE'),
            ('return', 'NOPE'),
        ):
            with self.subTest(args=args), self.assertRaises(CommandError):
                self.call(*args)


class AdminTests(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        self.client.force_login(self.admin)

    def test_settle_dues_action_is_atomic_and_audited(self):
        settled = Student.objects.create(name='Ravi', roll_no='R002')
        clear = Account.objects.create(student=settled, due=Decimal('0'))

        response = self.client.post(reverse('admin:account_account_changelist'), {
            'action': 'settle_dues',
            '_selected_action': [self.account.pk, clear.pk],
        }, follow=True)

        self.assertContains(response, 'Settled dues for 1 account(s).')
        self.reload()
        self.assertEqual(self.account.due, Decimal('0.00'))
        self.assertEqual(self.account.fees_paid, Decimal('600.00'))
        log = AuditLog.objects.get()
        self.assertEqual(log.user, self.admin)

    def test_audit_log_admin_is_read_only(self):
        record_payment(self.account, '10', self.user)
        log = AuditLog.objects.get()

        self.assertEqual(self.client.get(reverse('admin:account_auditlog_changelist')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:account_auditlog_change', args=[log.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:account_auditlog_add')).status_code, 403)
        self.assertEqual(self.client.post(reverse('admin:account_auditlog_delete', args=[log.pk]), {'post': 'yes'}).status_code, 403)
        self.assertTrue(AuditLog.objects.filter(pk=log.pk).exists())
