from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from account.models import Account
from faculty.models import Faculty
from hostel.models import Hostel
from library.models import Library
from student.models import Student

SMALL = 3
LARGE = 25


def seed(count, offset=0):
    for i in range(offset, offset + count):
        student = Student.objects.create(
            name=f"Student {i}", roll_no=f"R{i:04d}", branch="CSE" if i % 2 else "IT",
            physics=i, chemistry=i * 2, maths=i * 3,
        )
        book = Library.objects.create(
            book_id=f"B{i:04d}", title=f"Book {i}", author=f"Author {i}", issued_to=student,
        )
        Account.objects.create(student=student, library=book, fees_paid=Decimal("100"), due=Decimal(i))
        Hostel.objects.create(hostel_id=f"H{i:04d}", name=f"Hostel {i}", warden="Warden", capacity=100)
        Faculty.objects.create(emp_id=f"E{i:04d}", name=f"Faculty {i}", department="CSE", email=f"f{i}@example.com")


class QueryCountTestCase(TestCase):
    def count_queries(self, func):
        with CaptureQueriesContext(connection) as ctx:
            func()
        return len(ctx.captured_queries)

    def count_get(self, url):
        def fetch():
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
        return self.count_queries(fetch)

    def assertConstantQueries(self, url, expected):
        seed(SMALL)
        small = self.count_get(url)
        seed(LARGE - SMALL, offset=SMALL)
        large = self.count_get(url)
        self.assertEqual(small, large, f"{url} query count grew with row count ({small} -> {large})")
        self.assertEqual(large, expected)


class ListingQueryBenchmarkTests(QueryCountTestCase):
    def test_unoptimized_account_listing_is_n_plus_one(self):
        seed(LARGE)

        naive = self.count_queries(lambda: [a.student.name for a in Account.objects.all()])
        optimized = self.count_queries(lambda: [a.student.name for a in Account.objects.select_related("student")])

        self.assertEqual(naive, LARGE + 1)
        self.assertEqual(optimized, 1)

    def test_accounts_page_uses_single_query(self):
        self.assertConstantQueries(reverse("accounts"), 1)

    def test_accounts_page_renders_student_names(self):
        seed(SMALL)
        response = self.client.get(reverse("accounts"))
        for i in range(SMALL):
            self.assertContains(response, f"Student {i}")

    def test_books_page_uses_single_query(self):
        self.assertConstantQueries(reverse("books"), 1)

    def test_other_listing_pages_use_single_query(self):
        seed(LARGE)
        for name in ("students", "hostels", "faculty"):
            with self.subTest(page=name):
                self.assertEqual(self.count_get(reverse(name)), 1)

    def test_dashboard_query_count_is_constant(self):
        self.assertConstantQueries(reverse("dashboard"), 13)


class AdminQueryBenchmarkTests(QueryCountTestCase):
    def setUp(self):
        admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "pass")
        self.client.force_login(admin)

    def test_account_changelist_query_count_is_constant(self):
        seed(SMALL)
        small = self.count_get(reverse("admin:account_account_changelist"))
        seed(LARGE - SMALL, offset=SMALL)
        large = self.count_get(reverse("admin:account_account_changelist"))
        self.assertEqual(small, large)

    def test_library_changelist_query_count_is_constant(self):
        seed(SMALL)
        small = self.count_get(reverse("admin:library_library_changelist"))
        seed(LARGE - SMALL, offset=SMALL)
        large = self.count_get(reverse("admin:library_library_changelist"))
        self.assertEqual(small, large)


class DatabaseIndexTests(TestCase):
    EXPECTED = {
        Account: {"account_student_library_idx", "account_due_idx"},
        Library: {"library_issued_to_date_idx", "library_title_idx", "library_author_idx"},
        Student: {
            "student_branch_idx", "student_name_idx", "student_physics_desc_idx",
            "student_chemistry_desc_idx", "student_maths_desc_idx",
        },
        Faculty: {"faculty_department_idx"},
    }

    def test_indexes_are_declared_on_models(self):
        for model, names in self.EXPECTED.items():
            with self.subTest(model=model.__name__):
                self.assertTrue(names <= {index.name for index in model._meta.indexes})

    def test_indexes_exist_in_database(self):
        with connection.cursor() as cursor:
            for model, names in self.EXPECTED.items():
                constraints = connection.introspection.get_constraints(cursor, model._meta.db_table)
                with self.subTest(model=model.__name__):
                    self.assertTrue(names <= set(constraints))

    def test_foreign_keys_are_indexed(self):
        for model, field in ((Account, "student"), (Account, "library"), (Library, "issued_to")):
            with self.subTest(field=f"{model.__name__}.{field}"):
                self.assertTrue(model._meta.get_field(field).db_index)


class ProfileQueriesCommandTests(TestCase):
    def test_reports_query_count_per_page(self):
        seed(SMALL)
        out = StringIO()

        call_command("profile_queries", "accounts", "books", stdout=out)

        output = out.getvalue()
        self.assertIn("accounts", output)
        self.assertIn("queries=1", output)
        self.assertIn("books", output)

    def test_passes_within_budget(self):
        seed(SMALL)
        call_command("profile_queries", "--max-queries", "13", stdout=StringIO())

    def test_fails_when_budget_exceeded(self):
        with self.assertRaisesMessage(CommandError, "dashboard"):
            call_command("profile_queries", "dashboard", "--max-queries", "2", stdout=StringIO())

    def test_rejects_unknown_page(self):
        with self.assertRaises(CommandError):
            call_command("profile_queries", "nope")
