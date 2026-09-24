from smtplib import SMTPException
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from account.notifications import (
    NotificationDispatcher,
    UnknownEventError,
    build_message,
    notify_user,
    send_notification,
)

User = get_user_model()

LOCMEM_EMAIL = 'django.core.mail.backends.locmem.EmailBackend'

CUSTOM_TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'loaders': [
                ('django.template.loaders.locmem.Loader', {
                    'custom/notice.html': '<h2>Notice for {{ user_name }}</h2><p>{{ message }}</p>',
                }),
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]


@override_settings(EMAIL_BACKEND=LOCMEM_EMAIL, DEFAULT_FROM_EMAIL='library@example.com', LIBRARY_NAME='Test Library')
class SendNotificationTests(TestCase):
    def test_sends_to_recipient_with_rendered_subject(self):
        result = send_notification('overdue_reminder', 'reader@example.com', {
            'item_title': 'Clean Code',
            'due_date': '2026-09-01',
            'days_overdue': 3,
        })

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['reader@example.com'])
        self.assertEqual(message.subject, 'Overdue: Clean Code')
        self.assertEqual(message.from_email, 'library@example.com')

    def test_attaches_html_body_with_template_variables(self):
        send_notification('due_soon', ['a@example.com', 'b@example.com'], {
            'item_title': 'Refactoring',
            'due_date': '2026-10-05',
            'user_name': 'Asha',
        })

        message = mail.outbox[0]
        self.assertEqual(message.to, ['a@example.com', 'b@example.com'])
        self.assertEqual(message.subject, 'Reminder: Refactoring is due on 2026-10-05')
        html_body, mimetype = message.alternatives[0]
        self.assertEqual(mimetype, 'text/html')
        self.assertIn('<strong>Refactoring</strong>', html_body)
        self.assertIn('Hello Asha', html_body)
        self.assertIn('Test Library', html_body)
        self.assertNotIn('<strong>', message.body)
        self.assertIn('Refactoring', message.body)

    def test_escapes_html_in_body_but_not_subject(self):
        send_notification('due_soon', 'reader@example.com', {
            'item_title': 'Tom & <Jerry>',
            'due_date': 'tomorrow',
        })

        message = mail.outbox[0]
        self.assertEqual(message.subject, 'Reminder: Tom & <Jerry> is due on tomorrow')
        self.assertIn('Tom &amp; &lt;Jerry&gt;', message.alternatives[0][0])

    @override_settings(TEMPLATES=CUSTOM_TEMPLATES)
    def test_supports_custom_html_template_and_subject(self):
        send_notification(
            'account_status',
            'reader@example.com',
            {'user_name': 'Ravi', 'message': 'Library closes early today.', 'status': 'active'},
            subject='Notice for {{ user_name }}',
            template_name='custom/notice.html',
        )

        message = mail.outbox[0]
        self.assertEqual(message.subject, 'Notice for Ravi')
        self.assertEqual(
            message.alternatives[0][0],
            '<h2>Notice for Ravi</h2><p>Library closes early today.</p>',
        )

    def test_skips_when_no_recipients(self):
        with self.assertLogs('account.notifications', level='WARNING'):
            self.assertFalse(send_notification('due_soon', ['', '  '], {'item_title': 'X'}))
        self.assertEqual(mail.outbox, [])

    def test_logs_and_returns_false_when_backend_fails(self):
        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=SMTPException('down')):
            with self.assertLogs('account.notifications', level='ERROR') as logs:
                result = send_notification('due_soon', 'reader@example.com', {'item_title': 'X'})

        self.assertFalse(result)
        self.assertIn('Failed to send due_soon notification', logs.output[0])

    def test_logs_and_returns_false_when_template_missing(self):
        with self.assertLogs('account.notifications', level='ERROR'):
            result = send_notification('due_soon', 'reader@example.com', template_name='missing.html')
        self.assertFalse(result)

    def test_unknown_event_raises(self):
        with self.assertRaises(UnknownEventError):
            send_notification('not_an_event', 'reader@example.com')
        with self.assertRaises(UnknownEventError):
            build_message('not_an_event', 'reader@example.com')

    def test_notify_user_uses_user_email_and_name(self):
        user = User.objects.create_user('meera', 'meera@example.com', 'pass', first_name='Meera')

        self.assertTrue(notify_user(user, 'account_status', {'status': 'active'}))

        message = mail.outbox[0]
        self.assertEqual(message.to, ['meera@example.com'])
        self.assertEqual(message.subject, 'Your Test Library account is now active')
        self.assertIn('Hello Meera', message.alternatives[0][0])


@override_settings(EMAIL_BACKEND=LOCMEM_EMAIL)
class NotificationDispatcherTests(TestCase):
    def setUp(self):
        self.dispatcher = NotificationDispatcher(max_workers=2)
        self.addCleanup(self.dispatcher.shutdown)

    def test_dispatch_sends_in_background(self):
        futures = [
            self.dispatcher.dispatch('due_soon', 'one@example.com', {'item_title': 'A', 'due_date': 'Mon'}),
            self.dispatcher.dispatch('due_soon', 'two@example.com', {'item_title': 'B', 'due_date': 'Tue'}),
        ]

        self.assertEqual([future.result(timeout=5) for future in futures], [True, True])
        self.assertEqual(
            sorted(message.to[0] for message in mail.outbox),
            ['one@example.com', 'two@example.com'],
        )

    def test_dispatch_to_user(self):
        user = User.objects.create_user('kiran', 'kiran@example.com', 'pass')

        future = self.dispatcher.dispatch_to_user(user, 'account_status', {'status': 'active'})

        self.assertTrue(future.result(timeout=5))
        self.assertEqual(mail.outbox[0].to, ['kiran@example.com'])

    def test_dispatch_failure_is_logged_not_raised(self):
        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=SMTPException('down')):
            with self.assertLogs('account.notifications', level='ERROR'):
                future = self.dispatcher.dispatch('due_soon', 'reader@example.com', {'item_title': 'X'})
                self.assertFalse(future.result(timeout=5))

    def test_dispatch_unknown_event_raises_immediately(self):
        with self.assertRaises(UnknownEventError):
            self.dispatcher.dispatch('not_an_event', 'reader@example.com')


@override_settings(EMAIL_BACKEND=LOCMEM_EMAIL)
class SendNotificationCommandTests(TestCase):
    def test_command_sends_to_email_with_variables(self):
        call_command(
            'send_notification', 'overdue_reminder',
            '--to', 'reader@example.com',
            '--var', 'item_title=Dune',
            '--var', 'due_date=2026-09-10',
            stdout=mock.MagicMock(),
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['reader@example.com'])
        self.assertEqual(mail.outbox[0].subject, 'Overdue: Dune')

    def test_command_sends_to_user_in_background(self):
        User.objects.create_user('sam', 'sam@example.com', 'pass')

        call_command(
            'send_notification', 'account_status',
            '--user', 'sam',
            '--var', 'status=active',
            '--subject', 'Hi {{ user_name }}',
            '--background',
            stdout=mock.MagicMock(),
        )

        self.assertEqual(mail.outbox[0].to, ['sam@example.com'])
        self.assertEqual(mail.outbox[0].subject, 'Hi sam')

    def test_command_requires_recipient(self):
        with self.assertRaises(CommandError):
            call_command('send_notification', 'due_soon')

    def test_command_rejects_unknown_user(self):
        with self.assertRaises(CommandError):
            call_command('send_notification', 'due_soon', '--user', 'ghost')

    def test_command_rejects_invalid_variable(self):
        with self.assertRaises(CommandError):
            call_command('send_notification', 'due_soon', '--to', 'a@example.com', '--var', 'broken')


@override_settings(EMAIL_BACKEND=LOCMEM_EMAIL, ACCOUNT_STATUS_NOTIFICATIONS=True)
class AccountStatusSignalTests(TestCase):
    def setUp(self):
        patcher = mock.patch('account.signals.dispatcher.dispatch_to_user')
        self.dispatch = patcher.start()
        self.addCleanup(patcher.stop)
        self.user = User.objects.create_user('lee', 'lee@example.com', 'pass')

    def test_creating_user_does_not_notify(self):
        self.dispatch.assert_not_called()

    def test_deactivating_user_notifies(self):
        self.user.is_active = False
        self.user.save()

        self.dispatch.assert_called_once_with(self.user, 'account_status', {'status': 'deactivated'})

    def test_saving_without_status_change_does_not_notify(self):
        self.user.first_name = 'Lee'
        self.user.save()

        self.dispatch.assert_not_called()

    @override_settings(ACCOUNT_STATUS_NOTIFICATIONS=False)
    def test_disabled_setting_does_not_notify(self):
        self.user.is_active = False
        self.user.save()

        self.dispatch.assert_not_called()


@override_settings(EMAIL_BACKEND=LOCMEM_EMAIL, ACCOUNT_STATUS_NOTIFICATIONS=False)
class AdminActionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        self.client.force_login(self.admin)

    def test_action_sends_status_email_to_selected_users(self):
        active = User.objects.create_user('ann', 'ann@example.com', 'pass')
        inactive = User.objects.create_user('bob', 'bob@example.com', 'pass', is_active=False)
        no_email = User.objects.create_user('cat', '', 'pass')

        response = self.client.post(reverse('admin:auth_user_changelist'), {
            'action': 'send_account_status_email',
            '_selected_action': [active.pk, inactive.pk, no_email.pk],
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        subjects = {message.to[0]: message.subject for message in mail.outbox}
        self.assertEqual(len(subjects), 2)
        self.assertTrue(subjects['ann@example.com'].endswith('now active'))
        self.assertTrue(subjects['bob@example.com'].endswith('now deactivated'))
        self.assertContains(response, 'Skipped 1 user(s) without an email address.')
