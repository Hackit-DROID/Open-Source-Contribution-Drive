import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

EVENTS = {
    'enrollment_confirmed': {
        'subject': 'Enrollment confirmed: {{ course_id }} ({{ semester }} {{ year }})',
        'template': 'portal/emails/enrollment_confirmed.html',
    },
    'grade_posted': {
        'subject': 'Grade posted for {{ course_id }}',
        'template': 'portal/emails/grade_posted.html',
    },
    'deadline_reminder': {
        'subject': 'Reminder: {{ deadline_name }} is due on {{ deadline_date }}',
        'template': 'portal/emails/deadline_reminder.html',
    },
    'status_alert': {
        'subject': '{{ portal_name }} account update: {{ status }}',
        'template': 'portal/emails/status_alert.html',
    },
}


class UnknownEventError(ValueError):
    pass


def _normalize_recipients(recipients):
    if isinstance(recipients, str):
        recipients = [recipients]
    return [address.strip() for address in recipients or [] if address and address.strip()]


def _render_subject(subject_template, context):
    subject = Template('{% autoescape off %}' + subject_template + '{% endautoescape %}').render(Context(context))
    return ' '.join(subject.split())


def _html_to_text(html_body):
    text = strip_tags(re.sub(r'<head\b.*?</head>', '', html_body, flags=re.IGNORECASE | re.DOTALL))
    lines = [line.strip() for line in text.splitlines()]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()


def _record(event, recipients, subject, status, error=''):
    from portal.models import NotificationLog

    try:
        NotificationLog.objects.create(
            event=event,
            recipients=', '.join(recipients),
            subject=subject[:255],
            status=status,
            error=error,
        )
    except Exception:
        logger.exception('Could not record %s notification log entry', event)


def build_message(event, recipients, context=None, subject=None, template_name=None, from_email=None):
    if event not in EVENTS:
        raise UnknownEventError(f'Unknown notification event: {event}')

    config = EVENTS[event]
    full_context = {'portal_name': getattr(settings, 'PORTAL_NAME', 'University Portal')}
    full_context.update(context or {})

    html_body = render_to_string(template_name or config['template'], full_context)
    message = EmailMultiAlternatives(
        subject=_render_subject(subject or config['subject'], full_context),
        body=_html_to_text(html_body),
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=_normalize_recipients(recipients),
    )
    message.attach_alternative(html_body, 'text/html')
    return message


def send_notification(event, recipients, context=None, **options):
    if event not in EVENTS:
        raise UnknownEventError(f'Unknown notification event: {event}')

    addresses = _normalize_recipients(recipients)
    if not addresses:
        logger.warning('Skipping %s notification: no recipients', event)
        _record(event, addresses, '', 'skipped', 'No recipients')
        return False

    subject = ''
    try:
        message = build_message(event, addresses, context, **options)
        subject = message.subject
        sent = message.send(fail_silently=False) > 0
    except Exception as exc:
        logger.exception('Failed to send %s notification to %s', event, addresses)
        _record(event, addresses, subject, 'failed', f'{type(exc).__name__}: {exc}')
        return False

    _record(event, addresses, subject, 'sent' if sent else 'failed', '' if sent else 'Backend sent 0 messages')
    return sent


def student_context(student):
    return {
        'student': student,
        'recipient_name': student.name,
        'student_id': student.ID,
        'department': student.dept_name_id,
    }


def notify_student(student, event, context=None, **options):
    full_context = student_context(student)
    full_context.update(context or {})
    return send_notification(event, student.email, full_context, **options)


class NotificationDispatcher:
    def __init__(self, max_workers=None):
        self.max_workers = max_workers
        self._executor = None
        self._lock = threading.Lock()

    def _get_executor(self):
        with self._lock:
            if self._executor is None:
                workers = self.max_workers or getattr(settings, 'NOTIFICATION_MAX_WORKERS', 2)
                self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='notification')
            return self._executor

    def _submit(self, func, event, *args, **kwargs):
        if event not in EVENTS:
            raise UnknownEventError(f'Unknown notification event: {event}')
        return self._get_executor().submit(self._run, func, event, *args, **kwargs)

    @staticmethod
    def _run(func, event, *args, **kwargs):
        from django.db import close_old_connections

        try:
            return func(*args, **kwargs)
        finally:
            close_old_connections()

    def dispatch(self, event, recipients, context=None, **options):
        return self._submit(send_notification, event, event, recipients, context, **options)

    def dispatch_to_student(self, student, event, context=None, **options):
        return self._submit(notify_student, event, student, event, context, **options)

    def shutdown(self, wait=True):
        with self._lock:
            executor, self._executor = self._executor, None
        if executor is not None:
            executor.shutdown(wait=wait)


dispatcher = NotificationDispatcher()
