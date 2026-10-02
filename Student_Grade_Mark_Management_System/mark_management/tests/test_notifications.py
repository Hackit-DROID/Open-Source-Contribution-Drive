from datetime import datetime, timedelta

import pytest

from app import send_marks_pending_reminders
from models import db, Student, Marks, NotificationLog, SUBJECTS
from notifications import notifications, SMTPEmailBackend, EmailMessage


def create_student(email='asha@example.com', roll_no='CS001', created_at=None):
    student = Student(name='Asha Patil', roll_no=roll_no, branch='Computer Science (CSE)',
                      year='SY', email=email)
    if created_at:
        student.created_at = created_at
    db.session.add(student)
    db.session.commit()
    return student


def marks_form(t1=15, t2=15, final=45, overrides=None):
    form = {}
    for subject in SUBJECTS:
        form[f'{subject}_t1'] = t1
        form[f'{subject}_t2'] = t2
        form[f'{subject}_final'] = final
    form.update(overrides or {})
    return form


def test_add_student_sends_welcome_email(client, outbox):
    response = client.post('/add-student', data={
        'name': 'Asha Patil', 'roll_no': 'CS001', 'branch': 'Computer Science (CSE)',
        'year': 'SY', 'email': 'asha@example.com',
    })

    assert response.status_code == 302
    assert len(outbox) == 1
    message = outbox[0]
    assert message.to == ['asha@example.com']
    assert message.subject == 'Welcome to Marksheet Management System, Asha Patil!'
    assert 'CS001' in message.html_body
    assert message.headers['X-Notification-Event'] == 'student_registered'

    log = NotificationLog.query.one()
    assert log.status == NotificationLog.STATUS_SENT
    assert log.recipient == 'asha@example.com'
    assert log.sent_at is not None


def test_add_student_without_email_is_skipped(client, outbox):
    client.post('/add-student', data={
        'name': 'No Mail', 'roll_no': 'CS002', 'branch': 'Computer Science (CSE)', 'year': 'FY',
    })

    assert outbox == []
    log = NotificationLog.query.one()
    assert log.status == NotificationLog.STATUS_SKIPPED


def test_saving_passing_marks_sends_published_email_only(client, outbox):
    student = create_student()

    client.post(f'/marks/{student.id}', data=marks_form())

    assert len(outbox) == 1
    message = outbox[0]
    assert message.to == ['asha@example.com']
    assert message.subject == 'Your marks have been published (Pass)'
    assert 'http://testserver/report/' in message.html_body
    assert '375/500' in message.html_body


def test_saving_failing_marks_sends_academic_alert(client, outbox):
    student = create_student()

    client.post(f'/marks/{student.id}', data=marks_form(overrides={
        'Physics_t1': 5, 'Physics_t2': 5, 'Physics_final': 10,
    }))

    subjects = [m.subject for m in outbox]
    assert subjects == [
        'Your marks have been published (Fail)',
        'Academic alert: 1 subject(s) below passing marks',
    ]
    assert all(m.to == ['asha@example.com'] for m in outbox)
    assert 'Physics' in outbox[1].html_body


def test_invalid_marks_do_not_send_email(client, outbox):
    student = create_student()

    client.post(f'/marks/{student.id}', data=marks_form(t1=99))

    assert outbox == []


def test_render_supports_custom_template_variables(app):
    subject, html, _ = notifications.render(
        'marks_pending_reminder',
        'Hello {{ name }} from {{ app_name }}',
        {'name': 'Ravi', 'roll_no': 'ME042', 'days_waiting': 9},
    )

    assert subject == 'Hello Ravi from Marksheet Management System'
    assert 'ME042' in html
    assert '9 day(s)' in html
    assert '<html' in html


def test_render_escapes_html_in_context(app):
    _, html, _ = notifications.render('student_registered', 'Hi',
                                      {'name': '<script>x</script>', 'roll_no': '1', 'branch': 'b', 'year': 'y'})

    assert '<script>' not in html
    assert '&lt;script&gt;' in html


def test_backend_failure_is_logged_and_does_not_raise(app, monkeypatch, caplog):
    def boom(self, message):
        raise ConnectionError('smtp down')

    monkeypatch.setattr('notifications.LocmemEmailBackend.send', boom)
    student = create_student()

    log = notifications.send('student_registered', student.email, 'Hi {{ name }}', 'student_registered',
                             {'name': student.name, 'roll_no': student.roll_no,
                              'branch': student.branch, 'year': student.year},
                             student_id=student.id)

    assert log.status == NotificationLog.STATUS_FAILED
    assert 'smtp down' in log.error
    assert 'Failed to send "student_registered" notification' in caplog.text


def test_missing_template_is_logged_as_failure(app, outbox):
    log = notifications.send('custom', 'a@example.com', 'Subject', 'does_not_exist')

    assert outbox == []
    assert log.status == NotificationLog.STATUS_FAILED


def test_notifications_can_be_disabled(app, outbox):
    app.config['NOTIFICATIONS_ENABLED'] = False

    result = notifications.send('custom', 'a@example.com', 'Subject', 'student_registered')

    assert result is None
    assert outbox == []
    assert NotificationLog.query.count() == 0


def test_background_dispatcher_delivers_queued_messages(app, outbox):
    app.config['NOTIFICATIONS_ASYNC'] = True
    student = create_student()

    returned = notifications.dispatch('student_registered', student.email, 'Queued for {{ name }}',
                                      'student_registered',
                                      {'name': student.name, 'roll_no': student.roll_no,
                                       'branch': student.branch, 'year': student.year})
    notifications.flush()

    assert returned is None
    assert len(outbox) == 1
    assert outbox[0].to == ['asha@example.com']
    assert outbox[0].subject == 'Queued for Asha Patil'


def test_pending_marks_reminder_targets_overdue_students(app, outbox):
    old = datetime.utcnow() - timedelta(days=10)
    overdue = create_student(email='late@example.com', roll_no='CS010', created_at=old)
    create_student(email='new@example.com', roll_no='CS011')
    graded = create_student(email='done@example.com', roll_no='CS012', created_at=old)
    db.session.add(Marks(student_id=graded.id, subject='Physics', test1=10, test2=10, final_exam=30))
    db.session.commit()

    count = send_marks_pending_reminders(days=7)

    assert count == 1
    assert len(outbox) == 1
    assert outbox[0].to == [overdue.email]
    assert outbox[0].subject == 'Reminder: your marks are still pending'
    assert '10 day(s)' in outbox[0].html_body


def test_send_reminders_cli_command(app, outbox):
    create_student(email='late@example.com', roll_no='CS020',
                   created_at=datetime.utcnow() - timedelta(days=30))

    result = app.test_cli_runner().invoke(args=['send-reminders', '--days', '14'])

    assert result.exit_code == 0
    assert 'for 1 student(s)' in result.output
    assert [m.to for m in outbox] == [['late@example.com']]


def test_smtp_backend_builds_multipart_message():
    backend = SMTPEmailBackend('localhost', 25, use_tls=False)
    mime = backend.build_mime(EmailMessage(subject='Hello', to=['a@example.com'], html_body='<b>hi</b>',
                                           text_body='hi', from_email='noreply@example.com'))

    assert mime['Subject'] == 'Hello'
    assert mime['To'] == 'a@example.com'
    assert [part.get_content_type() for part in mime.get_payload()] == ['text/plain', 'text/html']


def test_smtp_backend_sends_via_smtplib(monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            sent['host'] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def starttls(self):
            sent['tls'] = True

        def login(self, user, password):
            sent['login'] = (user, password)

        def sendmail(self, from_addr, to_addrs, body):
            sent['to'] = to_addrs
            sent['body'] = body

    monkeypatch.setattr('notifications.smtplib.SMTP', FakeSMTP)
    SMTPEmailBackend('smtp.example.com', 587, 'user', 'pw').send(
        EmailMessage(subject='Hi', to=['a@example.com'], html_body='<p>x</p>', from_email='n@example.com'))

    assert sent['host'] == ('smtp.example.com', 587)
    assert sent['tls'] is True
    assert sent['login'] == ('user', 'pw')
    assert sent['to'] == ['a@example.com']
    assert 'Subject: Hi' in sent['body']
