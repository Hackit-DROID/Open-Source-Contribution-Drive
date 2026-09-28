from io import StringIO
from smtplib import SMTPException
from unittest import mock

from django.core import mail
from django.core.management import CommandError, call_command
from django.test import TestCase, TransactionTestCase, override_settings

from portal.models import Course, Department, NotificationLog, Student, Takes
from portal.notifications import (
    NotificationDispatcher,
    UnknownEventError,
    build_message,
    notify_student,
    send_notification,
)

LOCMEM_EMAIL = 'django.core.mail.backends.locmem.EmailBackend'

CUSTOM_TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'loaders': [
                ('django.template.loaders.locmem.Loader', {
                    'custom/notice.html': '<h2>Notice for {{ recipient_name }}</h2><p>{{ message }}</p>',
                }),
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

EMAIL_SETTINGS = {
    'EMAIL_BACKEND': LOCMEM_EMAIL,
    'DEFAULT_FROM_EMAIL': 'registrar@example.com',
    'PORTAL_NAME': 'Test University',
}


def make_department():
    return Department.objects.create(dept_name='Comp. Sci.', building='Taylor', budget=100000)


def make_student(dept, student_id=1001, email='asha@example.com', name='Asha'):
    return Student.objects.create(ID=student_id, name=name, dept_name=dept, tot_cred=30, email=email)


@override_settings(PORTAL_NOTIFICATIONS_ENABLED=False, **EMAIL_SETTINGS)
class SendNotificationTests(TestCase):
    def test_sends_to_recipient_with_rendered_subject(self):
        result = send_notification('enrollment_confirmed', 'asha@example.com', {
            'course_id': 'CS-101', 'sec_id': '1', 'semester': 'Fall', 'year': 2026,
        })

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['asha@example.com'])
        self.assertEqual(message.subject, 'Enrollment confirmed: CS-101 (Fall 2026)')
        self.assertEqual(message.from_email, 'registrar@example.com')

    def test_attaches_html_body_with_template_variables(self):
        send_notification('deadline_reminder', ['a@example.com', 'b@example.com'], {
            'deadline_name': 'Course registration',
            'deadline_date': '2026-10-05',
            'recipient_name': 'Ravi',
        })

        message = mail.outbox[0]
        self.assertEqual(message.to, ['a@example.com', 'b@example.com'])
        self.assertEqual(message.subject, 'Reminder: Course registration is due on 2026-10-05')
        html_body, mimetype = message.alternatives[0]
        self.assertEqual(mimetype, 'text/html')
        self.assertIn('<strong>Course registration</strong>', html_body)
        self.assertIn('Hello Ravi', html_body)
        self.assertIn('Test University', html_body)
        self.assertNotIn('<strong>', message.body)
        self.assertNotIn('<title>', message.body)
        self.assertIn('Course registration', message.body)

    def test_escapes_html_in_body_but_not_subject(self):
        send_notification('deadline_reminder', 'a@example.com', {
            'deadline_name': 'Fees & <Dues>', 'deadline_date': 'Friday',
        })

        message = mail.outbox[0]
        self.assertEqual(message.subject, 'Reminder: Fees & <Dues> is due on Friday')
        self.assertIn('Fees &amp; &lt;Dues&gt;', message.alternatives[0][0])

    @override_settings(TEMPLATES=CUSTOM_TEMPLATES)
    def test_supports_custom_html_template_and_subject(self):
        send_notification(
            'status_alert',
            'a@example.com',
            {'recipient_name': 'Meera', 'message': 'Library closes early today.', 'status': 'active'},
            subject='Notice for {{ recipient_name }}',
            template_name='custom/notice.html',
        )

        message = mail.outbox[0]
        self.assertEqual(message.subject, 'Notice for Meera')
        self.assertEqual(message.alternatives[0][0], '<h2>Notice for Meera</h2><p>Library closes early today.</p>')

    def test_records_sent_notification(self):
        send_notification('status_alert', 'a@example.com', {'status': 'active'})

        log = NotificationLog.objects.get()
        self.assertEqual(log.status, NotificationLog.STATUS_SENT)
        self.assertEqual(log.event, 'status_alert')
        self.assertEqual(log.recipients, 'a@example.com')
        self.assertEqual(log.subject, 'Test University account update: active')

    def test_skips_when_no_recipients(self):
        with self.assertLogs('portal.notifications', level='WARNING'):
            self.assertFalse(send_notification('status_alert', ['', '  ']))

        self.assertEqual(mail.outbox, [])
        self.assertEqual(NotificationLog.objects.get().status, NotificationLog.STATUS_SKIPPED)

    def test_logs_and_returns_false_when_backend_fails(self):
        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=SMTPException('down')):
            with self.assertLogs('portal.notifications', level='ERROR') as logs:
                result = send_notification('status_alert', 'a@example.com', {'status': 'active'})

        self.assertFalse(result)
        self.assertIn('Failed to send status_alert notification', logs.output[0])
        log = NotificationLog.objects.get()
        self.assertEqual(log.status, NotificationLog.STATUS_FAILED)
        self.assertIn('SMTPException: down', log.error)

    def test_logs_and_returns_false_when_template_missing(self):
        with self.assertLogs('portal.notifications', level='ERROR'):
            result = send_notification('status_alert', 'a@example.com', template_name='missing.html')

        self.assertFalse(result)
        self.assertEqual(NotificationLog.objects.get().status, NotificationLog.STATUS_FAILED)

    def test_log_write_failure_does_not_break_sending(self):
        with mock.patch('portal.models.NotificationLog.objects.create', side_effect=RuntimeError('db down')):
            with self.assertLogs('portal.notifications', level='ERROR'):
                self.assertTrue(send_notification('status_alert', 'a@example.com', {'status': 'active'}))
        self.assertEqual(len(mail.outbox), 1)

    def test_unknown_event_raises(self):
        with self.assertRaises(UnknownEventError):
            send_notification('not_an_event', 'a@example.com')
        with self.assertRaises(UnknownEventError):
            build_message('not_an_event', 'a@example.com')

    def test_notify_student_uses_student_email_and_name(self):
        student = make_student(make_department())

        self.assertTrue(notify_student(student, 'status_alert', {'status': 'on probation'}))

        message = mail.outbox[0]
        self.assertEqual(message.to, ['asha@example.com'])
        self.assertEqual(message.subject, 'Test University account update: on probation')
        self.assertIn('Hello Asha', message.alternatives[0][0])


@override_settings(PORTAL_NOTIFICATIONS_ENABLED=False, **EMAIL_SETTINGS)
class NotificationDispatcherTests(TransactionTestCase):
    def setUp(self):
        self.dispatcher = NotificationDispatcher(max_workers=2)
        self.addCleanup(self.dispatcher.shutdown)

    def test_dispatch_sends_in_background(self):
        futures = [
            self.dispatcher.dispatch('status_alert', 'one@example.com', {'status': 'active'}),
            self.dispatcher.dispatch('status_alert', 'two@example.com', {'status': 'active'}),
        ]

        self.assertEqual([future.result(timeout=5) for future in futures], [True, True])
        self.assertEqual(sorted(m.to[0] for m in mail.outbox), ['one@example.com', 'two@example.com'])

    def test_dispatch_to_student(self):
        student = make_student(make_department())

        future = self.dispatcher.dispatch_to_student(student, 'status_alert', {'status': 'active'})

        self.assertTrue(future.result(timeout=5))
        self.assertEqual(mail.outbox[0].to, ['asha@example.com'])

    def test_dispatch_failure_is_logged_not_raised(self):
        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=SMTPException('down')):
            with self.assertLogs('portal.notifications', level='ERROR'):
                future = self.dispatcher.dispatch('status_alert', 'a@example.com', {'status': 'x'})
                self.assertFalse(future.result(timeout=5))

    def test_dispatch_unknown_event_raises_immediately(self):
        with self.assertRaises(UnknownEventError):
            self.dispatcher.dispatch('not_an_event', 'a@example.com')


@override_settings(PORTAL_NOTIFICATIONS_ENABLED=True, **EMAIL_SETTINGS)
class EnrollmentSignalTests(TestCase):
    def setUp(self):
        patcher = mock.patch('portal.signals.dispatcher.dispatch_to_student')
        self.dispatch = patcher.start()
        self.addCleanup(patcher.stop)
        dept = make_department()
        Course.objects.create(course_id='CS-101', title='Intro. to Computer Science', dept_name=dept, credits=4)
        self.student = make_student(dept)

    def enroll(self, student=None, grade=''):
        with self.captureOnCommitCallbacks(execute=True):
            return Takes.objects.create(
                ID=student or self.student, course_id='CS-101', sec_id='1',
                semester='Fall', year=2026, grade=grade,
            )

    def test_enrollment_triggers_confirmation(self):
        self.enroll()

        self.dispatch.assert_called_once()
        student, event, context = self.dispatch.call_args.args
        self.assertEqual((student, event), (self.student, 'enrollment_confirmed'))
        self.assertEqual(context['course_title'], 'Intro. to Computer Science')
        self.assertEqual(context['credits'], 4)
        self.assertEqual((context['semester'], context['year']), ('Fall', 2026))

    def test_grade_change_triggers_grade_posted(self):
        takes = self.enroll()
        self.dispatch.reset_mock()

        takes.grade = 'A'
        with self.captureOnCommitCallbacks(execute=True):
            takes.save()

        student, event, context = self.dispatch.call_args.args
        self.assertEqual(event, 'grade_posted')
        self.assertEqual((context['grade'], context['previous_grade']), ('A', ''))

    def test_saving_same_grade_does_not_notify(self):
        takes = self.enroll(grade='B')
        self.dispatch.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            takes.save()

        self.dispatch.assert_not_called()

    def test_student_without_email_is_skipped(self):
        no_email = make_student(self.student.dept_name, student_id=1002, email='', name='Kiran')

        self.enroll(student=no_email)

        self.dispatch.assert_not_called()

    @override_settings(PORTAL_NOTIFICATIONS_ENABLED=False)
    def test_disabled_setting_does_not_notify(self):
        self.enroll()
        self.dispatch.assert_not_called()

    def test_rolled_back_enrollment_does_not_notify(self):
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            Takes.objects.create(ID=self.student, course_id='CS-101', sec_id='1', semester='Fall', year=2026, grade='')
        self.assertEqual(len(callbacks), 1)
        self.dispatch.assert_not_called()


@override_settings(PORTAL_NOTIFICATIONS_ENABLED=True, **EMAIL_SETTINGS)
class EnrollmentEmailEndToEndTests(TransactionTestCase):
    def test_enrollment_sends_real_email_through_dispatcher(self):
        dept = make_department()
        Course.objects.create(course_id='CS-101', title='Intro. to Computer Science', dept_name=dept, credits=4)
        student = make_student(dept)

        with mock.patch('portal.signals.dispatcher') as patched:
            dispatcher = NotificationDispatcher(max_workers=1)
            self.addCleanup(dispatcher.shutdown)
            futures = []
            patched.dispatch_to_student.side_effect = (
                lambda *args, **kwargs: futures.append(dispatcher.dispatch_to_student(*args, **kwargs))
            )
            Takes.objects.create(ID=student, course_id='CS-101', sec_id='1', semester='Fall', year=2026, grade='')

        self.assertTrue(futures[0].result(timeout=5))
        message = mail.outbox[0]
        self.assertEqual(message.to, ['asha@example.com'])
        self.assertEqual(message.subject, 'Enrollment confirmed: CS-101 (Fall 2026)')
        self.assertIn('Intro. to Computer Science', message.alternatives[0][0])


@override_settings(PORTAL_NOTIFICATIONS_ENABLED=False, **EMAIL_SETTINGS)
class SendNotificationCommandTests(TestCase):
    def setUp(self):
        self.dept = make_department()
        self.student = make_student(self.dept)

    def call(self, *args):
        out, err = StringIO(), StringIO()
        call_command('send_notification', *args, stdout=out, stderr=err)
        return out.getvalue(), err.getvalue()

    def test_command_sends_to_email_with_variables(self):
        out, _ = self.call(
            'deadline_reminder', '--to', 'x@example.com',
            '--var', 'deadline_name=Fee payment', '--var', 'deadline_date=2026-10-01',
        )

        self.assertIn('Sent 1 deadline_reminder notification(s).', out)
        self.assertEqual(mail.outbox[0].to, ['x@example.com'])
        self.assertEqual(mail.outbox[0].subject, 'Reminder: Fee payment is due on 2026-10-01')

    def test_command_notifies_department_and_skips_missing_emails(self):
        make_student(self.dept, student_id=1002, email='ravi@example.com', name='Ravi')
        make_student(self.dept, student_id=1003, email='', name='Kiran')

        out, err = self.call('deadline_reminder', '--department', 'Comp. Sci.',
                             '--var', 'deadline_name=Registration', '--var', 'deadline_date=Monday')

        self.assertEqual(sorted(m.to[0] for m in mail.outbox), ['asha@example.com', 'ravi@example.com'])
        self.assertIn('Sent 2', out)
        self.assertIn('Skipped 1 student(s) without an email address.', err)

    def test_command_errors(self):
        cases = [
            ('status_alert',),
            ('status_alert', '--student', '9999'),
            ('status_alert', '--department', 'Nowhere'),
            ('status_alert', '--to', 'a@example.com', '--var', 'broken'),
        ]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(CommandError):
                self.call(*args)


@override_settings(PORTAL_NOTIFICATIONS_ENABLED=False, **EMAIL_SETTINGS)
class SendNotificationBackgroundCommandTests(TransactionTestCase):
    def test_command_sends_to_student_in_background(self):
        make_student(make_department())

        call_command('send_notification', 'status_alert', '--student', '1001', '--var', 'status=active',
                     '--subject', 'Hi {{ recipient_name }}', '--background', stdout=StringIO())

        self.assertEqual(mail.outbox[0].to, ['asha@example.com'])
        self.assertEqual(mail.outbox[0].subject, 'Hi Asha')
        self.assertEqual(NotificationLog.objects.get().status, NotificationLog.STATUS_SENT)
