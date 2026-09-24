from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from account.notifications import EVENTS, dispatcher, notify_user, send_notification


class Command(BaseCommand):
    help = 'Send an HTML email notification for a library event.'

    def add_arguments(self, parser):
        parser.add_argument('event', choices=sorted(EVENTS))
        parser.add_argument('--to', action='append', default=[], dest='emails',
                            help='Recipient email address. Can be repeated.')
        parser.add_argument('--user', action='append', default=[], dest='usernames',
                            help='Username to notify. Can be repeated.')
        parser.add_argument('--var', action='append', default=[], dest='variables',
                            help='Template variable as key=value. Can be repeated.')
        parser.add_argument('--subject', help='Override the default subject template.')
        parser.add_argument('--background', action='store_true',
                            help='Send through the background dispatcher.')

    def handle(self, *args, **options):
        context = self._parse_variables(options['variables'])
        users = self._get_users(options['usernames'])
        emails = options['emails']

        if not emails and not users:
            raise CommandError('Provide at least one recipient with --to or --user.')

        extra = {'subject': options['subject']} if options['subject'] else {}
        event = options['event']

        if options['background']:
            futures = [dispatcher.dispatch(event, email, context, **extra) for email in emails]
            futures += [dispatcher.dispatch_to_user(user, event, context, **extra) for user in users]
            results = [future.result() for future in futures]
            dispatcher.shutdown()
        else:
            results = [send_notification(event, email, context, **extra) for email in emails]
            results += [notify_user(user, event, context, **extra) for user in users]

        sent = sum(1 for result in results if result)
        failed = len(results) - sent
        self.stdout.write(self.style.SUCCESS('Sent %d %s notification(s).' % (sent, event)))
        if failed:
            self.stderr.write(self.style.WARNING('%d notification(s) failed. Check the logs.' % failed))

    def _parse_variables(self, variables):
        context = {}
        for item in variables:
            key, separator, value = item.partition('=')
            if not separator or not key.strip():
                raise CommandError('Invalid --var "%s". Use key=value.' % item)
            context[key.strip()] = value
        return context

    def _get_users(self, usernames):
        if not usernames:
            return []
        User = get_user_model()
        users = list(User.objects.filter(username__in=usernames))
        missing = set(usernames) - {user.get_username() for user in users}
        if missing:
            raise CommandError('Unknown user(s): %s' % ', '.join(sorted(missing)))
        return users
