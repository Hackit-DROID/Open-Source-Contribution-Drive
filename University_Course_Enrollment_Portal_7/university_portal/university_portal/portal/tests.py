import csv
import io
import json
import os
import tempfile

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse

from portal.exporters import (
    DATASETS,
    ExportError,
    build_queryset,
    get_dataset,
    iter_csv,
    sanitize_cell,
    select_columns,
)
from portal.models import Course, Department, Instructor, Section, Student, Takes


def seed():
    cs = Department.objects.create(dept_name='Comp. Sci.', building='Taylor', budget=100000)
    bio = Department.objects.create(dept_name='Biology', building='Watson', budget=90000)
    Student.objects.create(ID=1001, name='Asha', dept_name=cs, tot_cred=102)
    Student.objects.create(ID=1002, name='Ravi', dept_name=cs, tot_cred=32)
    Student.objects.create(ID=1003, name='=HYPERLINK("http://evil")', dept_name=bio, tot_cred=60)
    Instructor.objects.create(ID=10, name='Srinivasan', dept_name=cs, salary=65000)
    course = Course.objects.create(course_id='CS-101', title='Intro. to Computer Science', dept_name=cs, credits=4)
    Section.objects.create(course_id=course, sec_id='1', semester='Fall', year=2026,
                           building='Packard', room_no='101', time_slot_id=1)
    Takes.objects.create(ID_id=1001, course_id='CS-101', sec_id='1', semester='Fall', year=2026, grade='A')
    Takes.objects.create(ID_id=1002, course_id='CS-101', sec_id='1', semester='Fall', year=2026, grade='B')


def read_csv(text):
    return list(csv.reader(io.StringIO(text)))


def streamed(response):
    return b''.join(response.streaming_content).decode('utf-8')


class CsvHeaderFormattingTests(TestCase):
    def test_every_dataset_header_uses_its_column_labels(self):
        for name, dataset in DATASETS.items():
            with self.subTest(dataset=name):
                rows = read_csv(''.join(iter_csv([], dataset.columns)))
                self.assertEqual(rows, [[column.header for column in dataset.columns]])

    def test_student_header_row(self):
        text = ''.join(iter_csv([], get_dataset('students').columns))
        self.assertEqual(text, 'Student ID,Name,Department,Total Credits\r\n')

    def test_header_labels_are_unique_and_non_empty(self):
        for name, dataset in DATASETS.items():
            headers = [column.header for column in dataset.columns]
            with self.subTest(dataset=name):
                self.assertTrue(all(header.strip() for header in headers))
                self.assertEqual(len(headers), len(set(headers)))

    def test_header_follows_selected_column_order(self):
        columns = select_columns(get_dataset('students'), ['total_credits', 'name'])
        self.assertEqual(read_csv(''.join(iter_csv([], columns)))[0], ['Total Credits', 'Name'])

    def test_header_can_be_omitted(self):
        seed()
        dataset = get_dataset('students')
        rows = read_csv(''.join(iter_csv(Student.objects.order_by('ID'), dataset.columns, include_header=False)))
        self.assertEqual(rows[0], ['1001', 'Asha', 'Comp. Sci.', '102'])

    def test_header_with_comma_is_quoted(self):
        from portal.exporters import Column

        text = ''.join(iter_csv([], [Column('a', 'Room, Building', 'building'), Column('b', 'Capacity', 'capacity')]))
        self.assertEqual(text, '"Room, Building",Capacity\r\n')


class ExporterTests(TestCase):
    def setUp(self):
        seed()

    def test_filters_are_applied(self):
        queryset, applied = build_queryset(get_dataset('students'), {'department': 'Comp. Sci.', 'min_credits': '50'})

        self.assertEqual([s.ID for s in queryset], [1001])
        self.assertEqual(applied, {'department': 'Comp. Sci.', 'min_credits': 50})

    def test_blank_filters_are_ignored(self):
        queryset, applied = build_queryset(get_dataset('students'), {'department': '', 'name': '  '})
        self.assertEqual(queryset.count(), 3)
        self.assertEqual(applied, {})

    def test_invalid_filters_raise(self):
        dataset = get_dataset('students')
        for filters in ({'unknown': 'x'}, {'min_credits': 'abc'}):
            with self.subTest(filters=filters), self.assertRaises(ExportError):
                build_queryset(dataset, filters)

    def test_unknown_dataset_and_columns_raise(self):
        with self.assertRaises(ExportError):
            get_dataset('grades')
        with self.assertRaises(ExportError):
            select_columns(get_dataset('students'), ['name', 'password'])

    def test_related_columns(self):
        dataset = get_dataset('enrollments')
        queryset, _ = build_queryset(dataset, {'grade': 'A'})
        rows = read_csv(''.join(iter_csv(queryset, dataset.columns)))
        self.assertEqual(rows[1], ['1001', 'Asha', 'CS-101', '1', 'Fall', '2026', 'A'])

    def test_formula_cells_are_neutralised(self):
        self.assertEqual(sanitize_cell('=SUM(A1:A2)'), "'=SUM(A1:A2)")
        self.assertEqual(sanitize_cell('+1'), "'+1")
        self.assertEqual(sanitize_cell('@cmd'), "'@cmd")
        self.assertEqual(sanitize_cell('Asha'), 'Asha')
        self.assertEqual(sanitize_cell(-5), -5)
        self.assertEqual(sanitize_cell(None), '')


class ExportViewTests(TestCase):
    def setUp(self):
        seed()
        self.staff = get_user_model().objects.create_user('staff', password='pass', is_staff=True)
        self.client.force_login(self.staff)

    def get(self, dataset, **params):
        return self.client.get(reverse('export_data', args=[dataset]), params)

    def test_csv_download_response(self):
        response = self.get('students')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertRegex(response['Content-Disposition'], r'^attachment; filename="students-\d{8}-\d{6}\.csv"$')
        rows = read_csv(streamed(response))
        self.assertEqual(rows[0], ['Student ID', 'Name', 'Department', 'Total Credits'])
        self.assertEqual(len(rows), 4)

    def test_csv_export_escapes_formula_injection(self):
        rows = read_csv(streamed(self.get('students', department='Biology')))
        self.assertEqual(rows[1][1], '\'=HYPERLINK("http://evil")')

    def test_csv_filters_columns_and_header_toggle(self):
        rows = read_csv(streamed(self.get('students', department='Comp. Sci.', columns='name,total_credits')))
        self.assertEqual(rows, [['Name', 'Total Credits'], ['Asha', '102'], ['Ravi', '32']])

        rows = read_csv(streamed(self.get('students', name='asha', header='0')))
        self.assertEqual(rows, [['1001', 'Asha', 'Comp. Sci.', '102']])

    def test_json_export_is_structured(self):
        response = self.get('enrollments', format='json', course_id='CS-101', year='2026')

        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('.json"', response['Content-Disposition'])
        data = json.loads(streamed(response))
        self.assertEqual(data['dataset'], 'enrollments')
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['filters'], {'course_id': 'CS-101', 'year': 2026})
        self.assertEqual(data['columns'][0], {'key': 'student_id', 'header': 'Student ID'})
        self.assertIn('generated_at', data)
        self.assertEqual(data['records'][0]['student_name'], 'Asha')
        self.assertEqual([r['grade'] for r in data['records']], ['A', 'B'])

    def test_json_export_with_no_results(self):
        data = json.loads(streamed(self.get('students', format='json', department='History')))
        self.assertEqual((data['count'], data['records']), (0, []))

    def test_bad_requests(self):
        self.assertEqual(self.get('students', format='xml').status_code, 400)
        self.assertEqual(self.get('students', bogus='1').status_code, 400)
        self.assertEqual(self.get('students', min_credits='lots').status_code, 400)
        self.assertEqual(self.get('students', columns='name,ssn').status_code, 400)
        self.assertEqual(self.get('grades').status_code, 404)

    def test_requires_staff(self):
        self.client.logout()
        self.assertEqual(self.get('students').status_code, 302)

        regular = get_user_model().objects.create_user('student', password='pass')
        self.client.force_login(regular)
        self.assertEqual(self.get('students').status_code, 302)

    def test_only_get_allowed(self):
        response = self.client.post(reverse('export_data', args=['students']))
        self.assertEqual(response.status_code, 405)


class AdminExportActionTests(TestCase):
    def setUp(self):
        seed()
        admin = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'pass')
        self.client.force_login(admin)

    def test_export_selected_students_as_csv(self):
        response = self.client.post(reverse('admin:portal_student_changelist'), {
            'action': 'export_as_csv',
            '_selected_action': ['1001', '1002'],
        })

        self.assertEqual(response.status_code, 200)
        rows = read_csv(streamed(response))
        self.assertEqual(rows[0], ['Student ID', 'Name', 'Department', 'Total Credits'])
        self.assertEqual([row[0] for row in rows[1:]], ['1001', '1002'])

    def test_export_selected_courses_as_json(self):
        response = self.client.post(reverse('admin:portal_course_changelist'), {
            'action': 'export_as_json',
            '_selected_action': ['CS-101'],
        })

        data = json.loads(streamed(response))
        self.assertEqual(data['dataset'], 'courses')
        self.assertEqual(data['records'], [{
            'course_id': 'CS-101', 'title': 'Intro. to Computer Science',
            'department': 'Comp. Sci.', 'credits': 4,
        }])


class ExportCommandTests(TestCase):
    def setUp(self):
        seed()

    def run_command(self, *args):
        out = io.StringIO()
        call_command('export_data', *args, stdout=out, stderr=io.StringIO())
        return out.getvalue()

    def test_csv_to_stdout_with_filters(self):
        rows = read_csv(self.run_command('students', '--filter', 'department=Comp. Sci.', '--filter', 'max_credits=50'))
        self.assertEqual(rows, [['Student ID', 'Name', 'Department', 'Total Credits'], ['1002', 'Ravi', 'Comp. Sci.', '32']])

    def test_json_to_stdout(self):
        data = json.loads(self.run_command('sections', '--format', 'json'))
        self.assertEqual(data['records'][0]['course_title'], 'Intro. to Computer Science')

    def test_writes_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'instructors.csv')
            self.run_command('instructors', '--output', path, '--columns', 'name,salary')
            with open(path, newline='', encoding='utf-8') as handle:
                self.assertEqual(list(csv.reader(handle)), [['Name', 'Salary'], ['Srinivasan', '65000']])

    def test_no_header_option(self):
        rows = read_csv(self.run_command('departments', '--no-header', '--filter', 'building=Watson'))
        self.assertEqual(rows, [['Biology', 'Watson', '90000']])

    def test_invalid_arguments(self):
        for args in (('students', '--filter', 'broken'), ('students', '--filter', 'ssn=1'), ('students', '--columns', 'ssn')):
            with self.subTest(args=args), self.assertRaises(CommandError):
                self.run_command(*args)
