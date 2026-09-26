from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext

from sggs import views

PAGES = {
    'dashboard': ('/', views.dashboard),
    'students': ('/students/', views.students),
    'hostels': ('/hostels/', views.hostels),
    'books': ('/books/', views.books),
    'accounts': ('/accounts/', views.accounts),
    'faculty': ('/faculty/', views.faculty),
}


class Command(BaseCommand):
    help = 'Render listing pages and report the number of SQL queries each one executes.'

    def add_arguments(self, parser):
        parser.add_argument('pages', nargs='*', help=f"Pages to profile. Choices: {', '.join(PAGES)}.")
        parser.add_argument('--max-queries', type=int,
                            help='Fail if any page executes more than this many queries.')
        parser.add_argument('--show-sql', action='store_true', help='Print every executed query.')

    def handle(self, *args, **options):
        names = options['pages'] or list(PAGES)
        unknown = [name for name in names if name not in PAGES]
        if unknown:
            raise CommandError(f"Unknown page(s): {', '.join(unknown)}")

        factory = RequestFactory()
        limit = options['max_queries']
        over_limit = []

        for name in names:
            path, view = PAGES[name]
            with CaptureQueriesContext(connection) as ctx:
                response = view(factory.get(path))
            count = len(ctx.captured_queries)
            self.stdout.write(f"{name:<10} {path:<12} status={response.status_code} queries={count}")
            if options['show_sql']:
                for query in ctx.captured_queries:
                    self.stdout.write(f"    {query['sql']}")
            if limit is not None and count > limit:
                over_limit.append(f"{name} ({count})")

        if over_limit:
            raise CommandError(f"Query budget of {limit} exceeded by: {', '.join(over_limit)}")
