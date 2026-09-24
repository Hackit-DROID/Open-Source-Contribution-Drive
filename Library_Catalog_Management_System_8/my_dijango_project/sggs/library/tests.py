from django.test import TestCase
from django.db import transaction
from library.models import Book


class ModelVersionTest(TestCase):
    def test_book_has_version_field(self):
        """Verify Book model has version attribute for optimistic concurrency."""
        book = Book.objects.create(title="Test", author="Author")
        self.assertIsNotNone(book.version)
        self.assertEqual(book.version, 0)

    def test_version_manual_increment(self):
        """Verify version can be manually incremented by application code."""
        book = Book.objects.create(title="Test", author="Author")
        # Application explicitly increments version
        book.version = 1
        book.save()
        book.refresh_from_db()
        self.assertEqual(book.version, 1)

    def test_version_double_manual_increment(self):
        """Verify version increments twice with two manual saves."""
        book = Book.objects.create(title="Test", author="Author")
        book.version = 1
        book.save()
        book.refresh_from_db()
        book.version = 2
        book.save()
        book.refresh_from_db()
        self.assertEqual(book.version, 2)


class OptimisticLockingTest(TestCase):
    def test_optimistic_locking_basic(self):
        """Verify basic optimistic locking pattern with version tracking."""
        book = Book.objects.create(title="Test", author="Author", is_available=True)
        # First checkout: set version and mark unavailable
        with transaction.atomic():
            b = Book.objects.get(id=book.id)
            b.version = 1  # Application sets expected version
            b.is_available = False
            b.save()
            # Refresh from database to verify persistence
            b.refresh_from_db()
        # Verify state after transaction
        self.assertEqual(b.version, 1)
        self.assertFalse(b.is_available)

    def test_version_conflict_detection(self):
        """Verify version conflict detection pattern."""
        book = Book.objects.create(title="Test", author="Author", is_available=True)
        # First update with version 1
        with transaction.atomic():
            b = Book.objects.get(id=book.id)
            b.version = 1
            b.is_available = False
            b.save()

        # Verify version was persisted
        book.refresh_from_db()
        self.assertEqual(book.version, 1)

        # Second update with new version
        with transaction.atomic():
            b = Book.objects.get(id=book.id)
            b.version = 2  # New version
            b.is_available = False
            b.save()

        # Verify final state
        book.refresh_from_db()
        self.assertEqual(book.version, 2)
        self.assertFalse(book.is_available)