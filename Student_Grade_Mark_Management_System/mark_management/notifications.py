import logging
import queue
import smtplib
import threading
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app, render_template, render_template_string
from jinja2 import TemplateNotFound

from models import db, NotificationLog

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    subject: str
    to: list
    html_body: str
    from_email: str
    text_body: str = ''
    headers: dict = field(default_factory=dict)


class ConsoleEmailBackend:
    def send(self, message):
        logger.info('Email to %s | %s\n%s', ', '.join(message.to), message.subject, message.text_body or message.html_body)


class LocmemEmailBackend:
    outbox = []

    def send(self, message):
        LocmemEmailBackend.outbox.append(message)


class SMTPEmailBackend:
    def __init__(self, host, port, username=None, password=None, use_tls=True, timeout=10):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.timeout = timeout

    def build_mime(self, message):
        mime = MIMEMultipart('alternative')
        mime['Subject'] = message.subject
        mime['From'] = message.from_email
        mime['To'] = ', '.join(message.to)
        for key, value in message.headers.items():
            mime[key] = value
        if message.text_body:
            mime.attach(MIMEText(message.text_body, 'plain', 'utf-8'))
        mime.attach(MIMEText(message.html_body, 'html', 'utf-8'))
        return mime

    def send(self, message):
        with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as server:
            if self.use_tls:
                server.starttls()
            if self.username:
                server.login(self.username, self.password)
            server.sendmail(message.from_email, message.to, self.build_mime(message).as_string())


class NotificationService:
    def __init__(self, app=None):
        self._queue = queue.Queue()
        self._worker = None
        self._lock = threading.Lock()
        self.app = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.config.setdefault('MAIL_BACKEND', 'console')
        app.config.setdefault('MAIL_SERVER', 'localhost')
        app.config.setdefault('MAIL_PORT', 587)
        app.config.setdefault('MAIL_USERNAME', None)
        app.config.setdefault('MAIL_PASSWORD', None)
        app.config.setdefault('MAIL_USE_TLS', True)
        app.config.setdefault('MAIL_DEFAULT_SENDER', 'noreply@marksheet.local')
        app.config.setdefault('NOTIFICATIONS_ENABLED', True)
        app.config.setdefault('NOTIFICATIONS_ASYNC', True)
        app.config.setdefault('APP_NAME', 'Marksheet Management System')
        app.config.setdefault('APP_BASE_URL', 'http://localhost:5001')
        app.extensions['notifications'] = self

    def get_backend(self):
        config = current_app.config
        name = str(config['MAIL_BACKEND']).lower()
        if name == 'smtp':
            return SMTPEmailBackend(
                host=config['MAIL_SERVER'],
                port=int(config['MAIL_PORT']),
                username=config['MAIL_USERNAME'],
                password=config['MAIL_PASSWORD'],
                use_tls=config['MAIL_USE_TLS'],
            )
        if name == 'locmem':
            return LocmemEmailBackend()
        return ConsoleEmailBackend()

    def build_context(self, context):
        base = {
            'app_name': current_app.config['APP_NAME'],
            'base_url': current_app.config['APP_BASE_URL'].rstrip('/'),
        }
        base.update(context or {})
        return base

    def render(self, template, subject, context):
        ctx = self.build_context(context)
        rendered_subject = render_template_string(subject, **ctx).strip()
        html_body = render_template(f'emails/{template}.html', subject=rendered_subject, **ctx)
        try:
            text_body = render_template(f'emails/{template}.txt', **ctx)
        except TemplateNotFound:
            text_body = ''
        return rendered_subject, html_body, text_body

    def send(self, event, recipient, subject, template, context=None, student_id=None):
        if not current_app.config['NOTIFICATIONS_ENABLED']:
            return None

        log = NotificationLog(event=event, recipient=recipient or '', subject=subject, student_id=student_id)

        if not recipient:
            log.status = NotificationLog.STATUS_SKIPPED
            log.error = 'No recipient email address'
            return self._save_log(log)

        try:
            rendered_subject, html_body, text_body = self.render(template, subject, context)
            log.subject = rendered_subject
            message = EmailMessage(
                subject=rendered_subject,
                to=[recipient],
                html_body=html_body,
                text_body=text_body,
                from_email=current_app.config['MAIL_DEFAULT_SENDER'],
                headers={'X-Notification-Event': event},
            )
            self.get_backend().send(message)
            log.mark_sent()
        except Exception as exc:
            logger.exception('Failed to send "%s" notification to %s', event, recipient)
            log.status = NotificationLog.STATUS_FAILED
            log.error = str(exc)[:500]

        return self._save_log(log)

    def _save_log(self, log):
        try:
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('Failed to record notification log for "%s"', log.event)
        return log

    def dispatch(self, event, recipient, subject, template, context=None, student_id=None):
        payload = dict(event=event, recipient=recipient, subject=subject,
                       template=template, context=context or {}, student_id=student_id)
        if not current_app.config['NOTIFICATIONS_ASYNC']:
            return self.send(**payload)
        self._ensure_worker()
        self._queue.put(payload)
        return None

    def _ensure_worker(self):
        with self._lock:
            if self._worker is None or not self._worker.is_alive():
                self._worker = threading.Thread(target=self._run, name='notification-dispatcher', daemon=True)
                self._worker.start()

    def _run(self):
        app = self.app
        while True:
            payload = self._queue.get()
            try:
                with app.app_context():
                    self.send(**payload)
            except Exception:
                logger.exception('Notification dispatcher failed for "%s"', payload.get('event'))
            finally:
                self._queue.task_done()

    def flush(self):
        self._queue.join()


notifications = NotificationService()


def absolute_url(path):
    return current_app.config['APP_BASE_URL'].rstrip('/') + path


def notify_student_registered(student):
    return notifications.dispatch(
        event='student_registered',
        recipient=student.email,
        subject='Welcome to {{ app_name }}, {{ name }}!',
        template='student_registered',
        context={
            'name': student.name,
            'roll_no': student.roll_no,
            'branch': student.branch,
            'year': student.year,
        },
        student_id=student.id,
    )


def notify_marks_published(student, summary):
    return notifications.dispatch(
        event='marks_published',
        recipient=student.email,
        subject='Your marks have been published ({{ result }})',
        template='marks_published',
        context={
            'name': student.name,
            'roll_no': student.roll_no,
            'report_url': absolute_url(f'/report/{student.id}'),
            **summary,
        },
        student_id=student.id,
    )


def notify_academic_alert(student, summary):
    return notifications.dispatch(
        event='academic_alert',
        recipient=student.email,
        subject='Academic alert: {{ failed_subjects|length }} subject(s) below passing marks',
        template='academic_alert',
        context={
            'name': student.name,
            'roll_no': student.roll_no,
            'report_url': absolute_url(f'/report/{student.id}'),
            **summary,
        },
        student_id=student.id,
    )


def notify_marks_pending(student, days_waiting):
    return notifications.dispatch(
        event='marks_pending_reminder',
        recipient=student.email,
        subject='Reminder: your marks are still pending',
        template='marks_pending_reminder',
        context={
            'name': student.name,
            'roll_no': student.roll_no,
            'days_waiting': days_waiting,
        },
        student_id=student.id,
    )
