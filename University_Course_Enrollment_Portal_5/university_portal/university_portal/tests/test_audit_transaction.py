"""
Test suite for database transactional atomicity and audit logging in
University_Course_Enrollment_Portal_5.

Verifies:
- Multi-statement update wrapped in transaction.atomic().
- Automatic rollback if error occurs during execution.
- Audit log entry created capturing user ID, timestamp, and action detail.
"""
import os
import sys
import django
from django.test import TestCase

# Configure Django settings before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "university_portal.settings")
PROJECT_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
)
sys.path.insert(0, PROJECT_ROOT)
django.setup()

from portal.models import Department, Course, Student, Takes, AuditLog
from manage import (
    execute_atomic_with_audit,
    atomic_student_enrollment_and_credits,
    atomic_department_budget_update,
)


class TestTransactionalAtomicityAndAudit(TestCase):
    """Test atomic transactions and audit logging engine."""

    def setUp(self):
        self.dept = Department.objects.create(
            dept_name="CS", building="Taylor", budget=100000
        )
        self.course = Course.objects.create(
            course_id="CS101", title="Intro to CS", dept_name=self.dept, credits=4
        )
        self.student = Student.objects.create(
            ID=1001, name="Alice", dept_name=self.dept, tot_cred=30
        )

    def test_successful_atomic_transaction_creates_audit_log(self):
        """Successful multi-statement update commits changes and creates audit log."""
        takes, log_entry = atomic_student_enrollment_and_credits(
            user_id="registrar_user_42",
            student_id=1001,
            course_id="CS101",
            sec_id="1",
            semester="Fall",
            year=2024,
            grade="A",
            added_credits=4,
        )

        # Verify state mutations committed
        self.student.refresh_from_db()
        self.assertEqual(self.student.tot_cred, 34)
        self.assertTrue(Takes.objects.filter(ID=self.student, course_id="CS101").exists())

        # Verify audit log captures user_id, timestamp, action, and detail
        self.assertIsNotNone(log_entry.id)
        self.assertEqual(log_entry.user_id, "registrar_user_42")
        self.assertEqual(log_entry.action, "STUDENT_ENROLLMENT")
        self.assertIn("1001", log_entry.detail)
        self.assertIn("CS101", log_entry.detail)
        self.assertIsNotNone(log_entry.timestamp)

    def test_rollback_on_error_leaves_db_unchanged(self):
        """Database changes are automatically rolled back if an error occurs."""
        initial_budget = self.dept.budget
        initial_course_count = Course.objects.count()
        initial_audit_count = AuditLog.objects.count()

        def _faulty_mutation():
            # First statement: update department budget
            dept = Department.objects.get(dept_name="CS")
            dept.budget = 999999
            dept.save()

            # Second statement: create a course
            Course.objects.create(
                course_id="CS999", title="Faulty Course", dept_name=dept, credits=3
            )

            # Simulated failure mid-transaction
            raise RuntimeError("Database connection interrupted during mutation!")

        with self.assertRaises(RuntimeError):
            execute_atomic_with_audit(
                user_id="admin_test",
                action="FAULTY_MUTATION",
                detail="Should roll back completely",
                mutation_fn=_faulty_mutation,
            )

        # Verify full rollback: department budget reverted
        self.dept.refresh_from_db()
        self.assertEqual(self.dept.budget, initial_budget)

        # Verify full rollback: course not saved
        self.assertEqual(Course.objects.count(), initial_course_count)
        self.assertFalse(Course.objects.filter(course_id="CS999").exists())

        # Verify full rollback: no audit log committed for aborted transaction
        self.assertEqual(AuditLog.objects.count(), initial_audit_count)

    def test_atomic_department_budget_update_success(self):
        """Verify atomic department budget update commits and audits."""
        _, log = atomic_department_budget_update(
            user_id="finance_admin_1",
            dept_name="CS",
            new_budget=175000,
            note="Q4 allocation",
        )

        self.dept.refresh_from_db()
        self.assertEqual(self.dept.budget, 175000)
        self.assertEqual(log.user_id, "finance_admin_1")
        self.assertEqual(log.action, "DEPARTMENT_BUDGET_UPDATE")
        self.assertIn("175000", log.detail)
        self.assertIn("Q4 allocation", log.detail)

    def test_audit_log_model_fields(self):
        """Verify AuditLog model field declarations."""
        log = AuditLog.objects.create(
            user_id="user_test_99",
            action="TEST_ACTION",
            detail="Test detail message",
        )
        self.assertEqual(log.user_id, "user_test_99")
        self.assertEqual(log.action, "TEST_ACTION")
        self.assertEqual(log.detail, "Test detail message")
        self.assertIsNotNone(log.timestamp)
        self.assertIn("user_test_99", str(log))


if __name__ == "__main__":
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    failures = runner.run_tests(["tests"])
    sys.exit(bool(failures))
