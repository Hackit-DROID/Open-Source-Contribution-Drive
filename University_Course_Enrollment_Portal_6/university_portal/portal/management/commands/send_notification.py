from django.core.management.base import BaseCommand, CommandError

from portal.models import Student
from portal.notifications import EVENTS, dispatcher, notify_student, send_notification


class Command(BaseCommand):
    help = 'Send an HTML email notification for a portal event.'

    def add_arguments(self, parser):
        parser.add_argument('event', choices=sorted(EVENTS))
        parser.add_argument('--to', action='append', default=[], dest='emails',
                            help='Recipient email address. Can be repeated.')
        parser.add_argument('--student', action='append', default=[], dest='student_ids', type=int,
                            help='Student ID to notify. Can be repeated.')
        parser.add_argument('--department', help='Notify every student in this department.')
        parser.add_argument('--var', action='append', default=[], dest='variables',
                            help='Template variable as key=value. Can be repeated.')
        parser.add_argument('--subject', help='Override the default subject template.')
        parser.add_argument('--template', dest='template_name', help='Override the HTML template path.')
        parser.add_argument('--background', action='store_true',
                            help='Send through the background dispatcher.')

    def handle(self, *args, **options):
        context = self._parse_variables(options['variables'])
        students = self._get_students(options['student_ids'], options['department'])
        emails = options['emails']

        if not emails and not students:
            raise CommandError('Provide at least one recipient with --to, --student or --department.')

        extra = {key: options[key] for key in ('subject', 'template_name') if options[key]}
        event = options['event']
        without_email = [student for student in students if not student.email]
        students = [student for student in students if student.email]

        if options['background']:
            futures = [dispatcher.dispatch(event, email, context, **extra) for email in emails]
            futures += [dispatcher.dispatch_to_student(s, event, context, **extra) for s in students]
            results = [future.result() for future in futures]
            dispatcher.shutdown()
        else:
            results = [send_notification(event, email, context, **extra) for email in emails]
            results += [notify_student(s, event, context, **extra) for s in students]

        sent = sum(1 for result in results if result)
        failed = len(results) - sent
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} {event} notification(s).'))
        if without_email:
            self.stderr.write(self.style.WARNING(
                f'Skipped {len(without_email)} student(s) without an email address.'
            ))
        if failed:
            self.stderr.write(self.style.WARNING(f'{failed} notification(s) failed. Check the logs.'))

    def _parse_variables(self, variables):
        context = {}
        for item in variables:
            key, separator, value = item.partition('=')
            if not separator or not key.strip():
                raise CommandError(f'Invalid --var "{item}". Use key=value.')
            context[key.strip()] = value
        return context

    def _get_students(self, student_ids, department):
        students = {}
        if student_ids:
            found = {s.ID: s for s in Student.objects.filter(ID__in=student_ids)}
            missing = sorted(set(student_ids) - set(found))
            if missing:
                raise CommandError(f"Unknown student ID(s): {', '.join(map(str, missing))}")
            students.update(found)
        if department:
            in_department = Student.objects.filter(dept_name_id=department)
            if not in_department.exists():
                raise CommandError(f'No students found in department "{department}".')
            students.update({s.ID: s for s in in_department})
        return list(students.values())
