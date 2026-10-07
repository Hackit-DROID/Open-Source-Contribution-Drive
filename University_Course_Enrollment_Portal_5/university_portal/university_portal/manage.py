#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def execute_atomic_with_audit(user_id, action, detail, mutation_fn):
    """
    Executes a multi-statement mutation inside a transaction.atomic() block.

    If all statements in mutation_fn succeed, an immutable AuditLog entry
    is created capturing user_id, timestamp, action, and detail.

    If any statement or exception occurs, the entire transaction is rolled back
    automatically, ensuring database consistency, and the exception is re-raised.

    Args:
        user_id (str): ID of user performing the action.
        action (str): Description of the action (e.g. 'ENROLL_STUDENT', 'UPDATE_BUDGET').
        detail (str): Detailed metadata or state snapshot of the mutation.
        mutation_fn (callable): Callback function performing the database operations.

    Returns:
        The result of mutation_fn, and the created AuditLog instance.
    """
    from django.db import transaction
    from portal.models import AuditLog

    with transaction.atomic():
        result = mutation_fn()
        log_entry = AuditLog.objects.create(
            user_id=str(user_id),
            action=str(action),
            detail=str(detail)
        )
        return result, log_entry


def atomic_student_enrollment_and_credits(user_id, student_id, course_id, sec_id, semester, year, grade, added_credits):
    """
    Atomic multi-statement mutation:
    1. Records a course enrollment in Takes.
    2. Increments the student's total credits (tot_cred).
    3. Records an AuditLog entry with action detail.

    If an error occurs at any point, both database modifications are rolled back.
    """
    from portal.models import Student, Takes

    def _mutation():
        student = Student.objects.select_for_update().get(ID=student_id)
        takes = Takes.objects.create(
            ID=student,
            course_id=course_id,
            sec_id=sec_id,
            semester=semester,
            year=year,
            grade=grade,
        )
        student.tot_cred += added_credits
        student.save()
        return takes

    detail = f"Enrolled student {student_id} into {course_id}-{sec_id} ({semester} {year}) with {added_credits} credits"
    return execute_atomic_with_audit(user_id, "STUDENT_ENROLLMENT", detail, _mutation)


def atomic_department_budget_update(user_id, dept_name, new_budget, note=""):
    """
    Atomic multi-statement mutation:
    Updates department budget with validation and records an immutable AuditLog entry.
    Rolls back automatically on failure.
    """
    from portal.models import Department

    def _mutation():
        dept = Department.objects.select_for_update().get(dept_name=dept_name)
        old_budget = dept.budget
        dept.budget = new_budget
        dept.save()
        return old_budget, dept

    detail = f"Updated budget for {dept_name} to {new_budget}. Note: {note}"
    return execute_atomic_with_audit(user_id, "DEPARTMENT_BUDGET_UPDATE", detail, _mutation)


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_portal.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
