"""
Performance benchmark test suite for N+1 query optimization in
University_Course_Enrollment_Portal_4.

Verifies that:
- Instructors listing query count is reduced from N+1 to O(1).
- Sections timetable query count is reduced from N+1 to O(1).
- Foreign key and filter indexes are declared on models.
"""
import os
import sys
import django
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection

# Configure Django settings before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "university_portal.settings")
PROJECT_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
)
sys.path.insert(0, PROJECT_ROOT)
django.setup()

from portal.models import (
    Department,
    Classroom,
    Course,
    Instructor,
    Student,
    TimeSlot,
    Section,
    Teaches,
    Takes,
)
from manage import (
    get_optimized_instructors_with_courses,
    get_optimized_sections_with_timeslots,
    get_optimized_students,
    get_optimized_courses,
)


class TestQueryOptimization(TestCase):
    """Test reduction of query counts from N+1 to O(1)."""

    def setUp(self):
        # Create test departments
        self.dept_cs = Department.objects.create(
            dept_name="CS", building="Taylor", budget=100000
        )
        self.dept_ee = Department.objects.create(
            dept_name="EE", building="Packard", budget=80000
        )

        # Create test courses
        self.course1 = Course.objects.create(
            course_id="CS101", title="Intro to CS", dept_name=self.dept_cs, credits=4
        )
        self.course2 = Course.objects.create(
            course_id="CS201", title="Data Structures", dept_name=self.dept_cs, credits=4
        )

        # Create test instructors
        self.instructors = []
        for i in range(1, 6):
            inst = Instructor.objects.create(
                ID=100 + i,
                name=f"Professor {i}",
                dept_name=self.dept_cs if i % 2 == 0 else self.dept_ee,
                salary=75000 + (i * 1000),
            )
            self.instructors.append(inst)
            Teaches.objects.create(
                ID=inst,
                course_id="CS101",
                sec_id="1",
                semester="Fall",
                year=2024,
            )

        # Create test timeslots
        self.ts1 = TimeSlot.objects.create(
            time_slot_id=1, day="Mon", start_time=900, end_time=1000
        )
        self.ts2 = TimeSlot.objects.create(
            time_slot_id=2, day="Wed", start_time=1100, end_time=1200
        )

        # Create test sections
        for i in range(1, 6):
            Section.objects.create(
                course_id=self.course1 if i % 2 == 0 else self.course2,
                sec_id=str(i),
                semester="Fall",
                year=2024,
                building="Taylor",
                room_no="101",
                time_slot_id=1 if i % 2 == 0 else 2,
            )

    def test_instructors_query_count_reduced(self):
        """Verify instructor course retrieval runs in O(1) queries (2 queries) vs N+1 (6 queries)."""
        # Unoptimized simulation: 1 query for all instructors + 1 query per instructor for Teaches
        with CaptureQueriesContext(connection) as unopt_ctx:
            instructors = list(Instructor.objects.all())
            unopt_res = []
            for inst in instructors:
                teaches = list(Teaches.objects.filter(ID=inst))
                courses = [t.course_id for t in teaches]
                unopt_res.append({"instructor": inst, "courses": courses})

        unoptimized_queries = len(unopt_ctx)
        self.assertEqual(unoptimized_queries, 6)  # 1 + 5 = 6 (N+1)

        # Optimized query helper: 1 query for instructors with select_related + 1 for prefetch_related
        with CaptureQueriesContext(connection) as opt_ctx:
            opt_res = get_optimized_instructors_with_courses()

        optimized_queries = len(opt_ctx)
        self.assertEqual(optimized_queries, 2)  # O(1) constant 2 queries
        self.assertLess(optimized_queries, unoptimized_queries)
        self.assertEqual(len(opt_res), len(unopt_res))

    def test_sections_query_count_reduced(self):
        """Verify section timeslot retrieval runs in O(1) queries (2 queries) vs N+1 (6 queries)."""
        # Unoptimized simulation: 1 query for sections + 1 per section for timeslot
        with CaptureQueriesContext(connection) as unopt_ctx:
            sections = list(Section.objects.all())
            unopt_data = []
            for sec in sections:
                ts = TimeSlot.objects.filter(time_slot_id=sec.time_slot_id).first()
                unopt_data.append({"section": sec, "time_slot": ts})

        unoptimized_queries = len(unopt_ctx)
        self.assertEqual(unoptimized_queries, 6)  # 1 + 5 = 6 (N+1)

        # Optimized query helper: 1 query for sections + 1 for all timeslots
        with CaptureQueriesContext(connection) as opt_ctx:
            opt_data = get_optimized_sections_with_timeslots()

        optimized_queries = len(opt_ctx)
        self.assertEqual(optimized_queries, 2)  # O(1) constant 2 queries
        self.assertLess(optimized_queries, unoptimized_queries)
        self.assertEqual(len(opt_data), len(unopt_data))

    def test_students_select_related(self):
        """Verify students helper uses select_related for dept_name."""
        Student.objects.create(ID=1, name="Alice", dept_name=self.dept_cs, tot_cred=30)
        with CaptureQueriesContext(connection) as ctx:
            students = list(get_optimized_students())
            for s in students:
                _ = s.dept_name.dept_name  # accessing foreign key attribute
        self.assertEqual(len(ctx), 1)

    def test_courses_select_related(self):
        """Verify courses helper uses select_related for dept_name."""
        with CaptureQueriesContext(connection) as ctx:
            courses = list(get_optimized_courses())
            for c in courses:
                _ = c.dept_name.dept_name
        self.assertEqual(len(ctx), 1)


class TestDatabaseIndexes(TestCase):
    """Test that database indexes are declared on models."""

    def test_indexes_declared_on_models(self):
        # Department indexes
        dept_index_fields = [idx.fields for idx in Department._meta.indexes]
        self.assertIn(["building"], dept_index_fields)

        # Course indexes
        course_index_fields = [idx.fields for idx in Course._meta.indexes]
        self.assertIn(["title"], course_index_fields)
        self.assertIn(["dept_name"], course_index_fields)

        # Instructor indexes
        inst_index_fields = [idx.fields for idx in Instructor._meta.indexes]
        self.assertIn(["name"], inst_index_fields)
        self.assertIn(["dept_name"], inst_index_fields)

        # Student indexes
        student_index_fields = [idx.fields for idx in Student._meta.indexes]
        self.assertIn(["name"], student_index_fields)
        self.assertIn(["dept_name"], student_index_fields)

        # Section indexes
        section_index_fields = [idx.fields for idx in Section._meta.indexes]
        self.assertIn(["course_id"], section_index_fields)
        self.assertIn(["time_slot_id"], section_index_fields)

        # Teaches indexes
        teaches_index_fields = [idx.fields for idx in Teaches._meta.indexes]
        self.assertIn(["ID"], teaches_index_fields)
        self.assertIn(["course_id"], teaches_index_fields)

        # Takes indexes
        takes_index_fields = [idx.fields for idx in Takes._meta.indexes]
        self.assertIn(["ID"], takes_index_fields)
        self.assertIn(["course_id"], takes_index_fields)


if __name__ == "__main__":
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    failures = runner.run_tests(["tests"])
    sys.exit(bool(failures))
