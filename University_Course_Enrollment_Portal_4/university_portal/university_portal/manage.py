#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def get_optimized_instructors_with_courses():
    """
    Fetch all instructors with their teaching assignments in O(1) queries
    instead of N+1.

    Uses select_related for the department FK and prefetch_related for
    the reverse Teaches relationship, avoiding per-instructor queries.

    Returns:
        list[dict]: Each dict has 'instructor' and 'courses' keys.
    """
    from portal.models import Instructor

    instructors = Instructor.objects.select_related(
        'dept_name'
    ).prefetch_related(
        'teaches_set'
    ).all()

    result = []
    for instructor in instructors:
        courses = [teach.course_id for teach in instructor.teaches_set.all()]
        result.append({
            'instructor': instructor,
            'courses': courses,
        })
    return result


def get_optimized_sections_with_timeslots():
    """
    Fetch all sections with their time slots in O(1) queries instead of N+1.

    Pre-fetches all TimeSlot records and builds a lookup dict keyed by
    time_slot_id, eliminating per-section database hits.

    Returns:
        list[dict]: Each dict has 'section' and 'time_slot' keys.
    """
    from portal.models import Section, TimeSlot

    sections = Section.objects.select_related('course_id').all()

    # Build a lookup dict: time_slot_id -> first matching TimeSlot
    all_timeslots = TimeSlot.objects.all()
    timeslot_map = {}
    for ts in all_timeslots:
        if ts.time_slot_id not in timeslot_map:
            timeslot_map[ts.time_slot_id] = ts

    result = []
    for section in sections:
        result.append({
            'section': section,
            'time_slot': timeslot_map.get(section.time_slot_id),
        })
    return result


def get_optimized_students():
    """
    Fetch all students with their department pre-loaded via select_related.

    Returns:
        QuerySet: Students with dept_name already joined.
    """
    from portal.models import Student
    return Student.objects.select_related('dept_name').all()


def get_optimized_courses():
    """
    Fetch all courses with their department pre-loaded via select_related.

    Returns:
        QuerySet: Courses with dept_name already joined.
    """
    from portal.models import Course
    return Course.objects.select_related('dept_name').all()


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
