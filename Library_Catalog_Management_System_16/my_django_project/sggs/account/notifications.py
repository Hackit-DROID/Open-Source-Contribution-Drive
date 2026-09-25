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
    'overdue_reminder': {
        'subject': 'Overdue: {{ item_title }}',
        'template': 'account/emails/overdue_reminder.html',
    },
    'due_soon': {
        'subject': 'Reminder: {{ item_title }} is due on {{ due_date }}',
        'template': 'account/emails/due_soon.html',
    },
    'account_status': {
        'subject': 'Your {{ library_name }} account is now {{ status }}',
        'template': 'account/emails/account_status.html',
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


def build_message(event, recipients, context=None, subject=None, template_name=None, from_email=None):
    if event not in EVENTS:
        raise UnknownEventError('Unknown notification event: %s' % event)

    config = EVENTS[event]
    full_context = {'library_name': getattr(settings, 'LIBRARY_NAME', 'Library')}
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
    if not _normalize_recipients(recipients):
        logger.warning('Skipping %s notification: no recipients', event)
        return False

    try:
        message = build_message(event, recipients, context, **options)
        return message.send(fail_silently=False) > 0
    except UnknownEventError:
        raise
    except Exception:
        logger.exception('Failed to send %s notification to %s', event, recipients)
        return False


def notify_user(user, event, context=None, **options):
    full_context = {
        'user': user,
        'user_name': user.get_full_name() or user.get_username(),
    }
    full_context.update(context or {})
    return send_notification(event, user.email, full_context, **options)


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

    def dispatch(self, event, recipients, context=None, **options):
        if event not in EVENTS:
            raise UnknownEventError('Unknown notification event: %s' % event)
        return self._get_executor().submit(send_notification, event, recipients, context, **options)

    def dispatch_to_user(self, user, event, context=None, **options):
        if event not in EVENTS:
            raise UnknownEventError('Unknown notification event: %s' % event)
        return self._get_executor().submit(notify_user, user, event, context, **options)

    def shutdown(self, wait=True):
        with self._lock:
            executor, self._executor = self._executor, None
        if executor is not None:
            executor.shutdown(wait=wait)


dispatcher = NotificationDispatcher()
