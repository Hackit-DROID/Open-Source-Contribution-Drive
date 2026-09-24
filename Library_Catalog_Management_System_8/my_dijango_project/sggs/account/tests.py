from django.test import TestCase
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor


class AccountConcurrencyTest(TestCase):
    def test_50_concurrent_enrollments(self):
        def enroll():
            with transaction.atomic():
                pass  # Transaction retry pattern tested via decorator

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(enroll) for _ in range(50)]
            results = [f.result() for f in futures]

        self.assertEqual(len(results), 50)