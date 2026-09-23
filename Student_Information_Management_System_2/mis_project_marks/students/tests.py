from django.test import TestCase

from .views import get_grade


class GradeTests(TestCase):
    def test_grade_boundaries(self):
        self.assertEqual(get_grade(95), 'A+')
        self.assertEqual(get_grade(90), 'A+')
        self.assertEqual(get_grade(89.99), 'A')
        self.assertEqual(get_grade(80), 'A')
        self.assertEqual(get_grade(70), 'B')
        self.assertEqual(get_grade(60), 'C')
        self.assertEqual(get_grade(59.99), 'F')
        self.assertEqual(get_grade(0), 'F')
