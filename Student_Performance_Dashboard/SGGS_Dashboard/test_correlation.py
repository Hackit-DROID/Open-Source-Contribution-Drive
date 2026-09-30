import unittest
import os
import sys

# Ensure project modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, compute_pearson_correlation, get_attendance_performance_correlation
from database.db_setup import init_db, seed_data, get_connection


class AttendancePerformanceCorrelationTest(unittest.TestCase):
    """Test suite for CR-637: Attendance vs Academic Performance Correlation Analytics."""

    @classmethod
    def setUpClass(cls):
        # Initialize and seed database for testing
        init_db()
        seed_data()

    def setUp(self):
        self.client = app.test_client()

    # -------------------------------------------------------------------
    # 1. Pearson Correlation Math Tests
    # -------------------------------------------------------------------

    def test_perfect_positive_correlation(self):
        """Verify correlation coefficient is 1.0 for perfectly positive correlated arrays."""
        x = [10.0, 20.0, 30.0, 40.0, 50.0]
        y = [20.0, 40.0, 60.0, 80.0, 100.0]
        corr = compute_pearson_correlation(x, y)
        self.assertAlmostEqual(corr, 1.0, places=4)

    def test_perfect_negative_correlation(self):
        """Verify correlation coefficient is -1.0 for inversely correlated arrays."""
        x = [10.0, 20.0, 30.0, 40.0, 50.0]
        y = [100.0, 80.0, 60.0, 40.0, 20.0]
        corr = compute_pearson_correlation(x, y)
        self.assertAlmostEqual(corr, -1.0, places=4)

    def test_zero_variance_handles_gracefully(self):
        """Verify zero division is safely handled when values are constant."""
        x = [50.0, 50.0, 50.0]
        y = [60.0, 70.0, 80.0]
        corr = compute_pearson_correlation(x, y)
        self.assertEqual(corr, 0.0)

    def test_insufficient_data_returns_zero(self):
        """Verify correlation is 0.0 when less than 2 data points are provided."""
        self.assertEqual(compute_pearson_correlation([10.0], [20.0]), 0.0)
        self.assertEqual(compute_pearson_correlation([], []), 0.0)

    # -------------------------------------------------------------------
    # 2. Risk Student Flag Logic Tests
    # -------------------------------------------------------------------

    def test_risk_student_identification_logic(self):
        """Verify high risk is flagged ONLY when attendance < 75 AND marks < 50."""
        # Custom mock data check via get_attendance_performance_correlation
        data = get_attendance_performance_correlation()
        self.assertIn('risk_students', data)
        self.assertIn('scatter_plot_data', data)

        for student in data['risk_students']:
            self.assertLess(student['attendance_percentage'], 75.0)
            self.assertLess(student['marks_avg'], 50.0)
            self.assertTrue(student['is_risk'])

        for student in data['scatter_plot_data']:
            if student['attendance_percentage'] >= 75.0 or student['marks_avg'] >= 50.0:
                self.assertFalse(student['is_risk'])

    # -------------------------------------------------------------------
    # 3. API Endpoint Tests
    # -------------------------------------------------------------------

    def test_api_attendance_performance_correlation_success(self):
        """Verify GET /api/attendance_performance_correlation returns 200 and schema payload."""
        response = self.client.get('/api/attendance_performance_correlation')
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn('correlation_coefficient', data)
        self.assertIn('scatter_plot_data', data)
        self.assertIn('risk_students', data)
        self.assertIn('total_analyzed', data)
        self.assertIn('risk_count', data)

        self.assertIsInstance(data['correlation_coefficient'], (int, float))
        self.assertGreaterEqual(data['total_analyzed'], 0)
        self.assertEqual(data['risk_count'], len(data['risk_students']))

    def test_api_attendance_performance_correlation_branch_filter(self):
        """Verify filtering by branch restricts scatter plot data to that branch."""
        target_branch = "Computer Engineering"
        response = self.client.get(f'/api/attendance_performance_correlation?branch={target_branch}')
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        for student in data['scatter_plot_data']:
            self.assertEqual(student['branch'], target_branch)


if __name__ == '__main__':
    unittest.main()
