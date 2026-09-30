import os
import sys
import unittest
import numpy as np
import pandas as pd

# Ensure agent directory is in Python path for test execution
AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

from utils.scaler import MinMaxScaler, min_max_scale_column
from app import app
import app as app_module


class TestMinMaxScaler(unittest.TestCase):
    """Test suite verifying Min-Max Scaling and Normalization Engine (CR-808)."""

    def setUp(self):
        self.sample_df = pd.DataFrame({
            "age": [20, 30, 40, 50, 60],
            "salary": [20000.0, 40000.0, 60000.0, 80000.0, 100000.0],
            "constant_val": [5, 5, 5, 5, 5],
            "department": ["Engineering", "HR", "Engineering", "Marketing", "Sales"]
        })

    # -------------------------------------------------------------------
    # 1. Min and Max Computation Tests
    # -------------------------------------------------------------------

    def test_computes_min_and_max_values(self):
        """Verify scaler correctly computes min, max, and range for numerical columns."""
        scaler = MinMaxScaler()
        scaler.fit(self.sample_df, columns=["age", "salary"])

        self.assertIn("age", scaler.stats)
        self.assertIn("salary", scaler.stats)
        self.assertNotIn("department", scaler.stats)

        self.assertEqual(scaler.stats["age"]["min"], 20.0)
        self.assertEqual(scaler.stats["age"]["max"], 60.0)
        self.assertEqual(scaler.stats["age"]["range"], 40.0)

        self.assertEqual(scaler.stats["salary"]["min"], 20000.0)
        self.assertEqual(scaler.stats["salary"]["max"], 100000.0)
        self.assertEqual(scaler.stats["salary"]["range"], 80000.0)

    # -------------------------------------------------------------------
    # 2. Formula Application & Bounds Tests [0.0, 1.0]
    # -------------------------------------------------------------------

    def test_scaled_values_fall_between_zero_and_one(self):
        """Verify min-max formula (val - min) / (max - min) places all values in [0.0, 1.0]."""
        scaler = MinMaxScaler()
        scaled_df, stats = scaler.fit_transform(self.sample_df, columns=["age", "salary"])

        for col in ["age", "salary"]:
            col_values = scaled_df[col].tolist()
            # Verify min becomes 0.0, max becomes 1.0
            self.assertAlmostEqual(min(col_values), 0.0, places=6)
            self.assertAlmostEqual(max(col_values), 1.0, places=6)
            # Verify every intermediate value is bounded in [0.0, 1.0]
            for v in col_values:
                self.assertGreaterEqual(v, 0.0)
                self.assertLessEqual(v, 1.0)

    def test_specific_formula_values(self):
        """Verify exact mathematical values produced by the scaling formula."""
        scaler = MinMaxScaler()
        scaled_df = scaler.fit_transform(self.sample_df, columns=["age"])[0]
        # age: [20, 30, 40, 50, 60] -> [0.0, 0.25, 0.5, 0.75, 1.0]
        expected_age = [0.0, 0.25, 0.5, 0.75, 1.0]
        for actual, expected in zip(scaled_df["age"].tolist(), expected_age):
            self.assertAlmostEqual(actual, expected, places=5)

    def test_constant_column_safe_fallback(self):
        """Verify columns with identical min and max do not cause ZeroDivisionError."""
        scaler = MinMaxScaler()
        scaled_df = scaler.fit_transform(self.sample_df, columns=["constant_val"])[0]
        self.assertEqual(scaled_df["constant_val"].tolist(), [0.0, 0.0, 0.0, 0.0, 0.0])

    # -------------------------------------------------------------------
    # 3. 1D Array / Series Scaling Tests
    # -------------------------------------------------------------------

    def test_min_max_scale_column_helper(self):
        """Verify min_max_scale_column standalone helper produces expected scaled floats."""
        raw_vals = [10, 20, 30, 40, 50]
        scaled = min_max_scale_column(raw_vals)
        self.assertEqual(scaled, [0.0, 0.25, 0.5, 0.75, 1.0])

    # -------------------------------------------------------------------
    # 4. API Endpoint Integration Tests
    # -------------------------------------------------------------------

    def test_normalize_api_endpoint(self):
        """Verify POST /normalize returns scaled sample and stats dictionary."""
        client = app.test_client()
        # Set global df for test
        app_module.df_global = self.sample_df.copy()

        response = client.post("/normalize", json={"columns": ["age", "salary"]})
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("columns_scaled", data)
        self.assertIn("stats", data)
        self.assertIn("age", data["stats"])
        self.assertIn("salary", data["stats"])

        # Check sample records
        sample = data["sample"]
        self.assertEqual(len(sample), 5)
        self.assertEqual(sample[0]["age"], 0.0)
        self.assertEqual(sample[-1]["age"], 1.0)


if __name__ == "__main__":
    unittest.main()
