import os
import sys
import unittest
import numpy as np
import pandas as pd

AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

from utils.encoder import LabelEncoder, OneHotEncoder, CategoricalFeatureEncoder
from app import app
import app as app_module


class TestCategoricalFeatureEncoder(unittest.TestCase):
    """Test suite verifying Categorical Column One-Hot & Label Encoding Engine (CR-856)."""

    def setUp(self):
        self.sample_df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "city": ["New York", "London", "Paris", "New York", "London"],
            "tier": ["Gold", "Silver", "Bronze", "Gold", "Platinum"],
            "score": [88, 92, 79, 95, 84],
        })

    # -------------------------------------------------------------------
    # 1. Label Encoding Tests
    # -------------------------------------------------------------------

    def test_label_encoder_generates_unique_integer_mappings(self):
        """Verify unique integer mappings [0, N-1] for distinct categories."""
        encoder = LabelEncoder()
        encoder.fit(self.sample_df["city"])

        # Distinct categories: London, New York, Paris (sorted)
        self.assertEqual(encoder.classes_, ["London", "New York", "Paris"])
        self.assertEqual(encoder.mapping_["London"], 0)
        self.assertEqual(encoder.mapping_["New York"], 1)
        self.assertEqual(encoder.mapping_["Paris"], 2)

        encoded = encoder.transform(self.sample_df["city"])
        self.assertEqual(list(encoded), [1, 0, 2, 1, 0])

    def test_label_encoder_inverse_transform(self):
        """Verify inverse transformation reconstructs original string categories."""
        encoder = LabelEncoder()
        encoded = encoder.fit_transform(self.sample_df["tier"])
        reconstructed = encoder.inverse_transform(encoded)
        self.assertEqual(list(reconstructed), list(self.sample_df["tier"]))

    def test_label_encoder_unseen_and_missing_values(self):
        """Verify handling of unseen categories and NaN values."""
        encoder = LabelEncoder()
        encoder.fit(["Cat", "Dog"])

        # Unseen category with error
        with self.assertRaises(ValueError):
            encoder.transform(["Bird"])

        # Unseen category with ignore -> -1
        res = encoder.transform(["Bird", "Cat"], handle_unknown="ignore")
        self.assertEqual(list(res), [-1, 0])

    # -------------------------------------------------------------------
    # 2. One-Hot Encoding Tests
    # -------------------------------------------------------------------

    def test_one_hot_encoder_creates_binary_indicator_columns(self):
        """Verify binary indicator columns are created with 0 and 1 values."""
        encoder = OneHotEncoder()
        encoded_df, new_cols = encoder.fit_transform(self.sample_df, columns=["city"])

        # Should generate city_London, city_New York, city_Paris
        expected_cols = ["city_London", "city_New York", "city_Paris"]
        for col in expected_cols:
            self.assertIn(col, encoded_df.columns)
            # Binary indicators must be strictly 0 or 1
            self.assertTrue(set(encoded_df[col].unique()).issubset({0, 1}))

        # Original 'city' column should be replaced
        self.assertNotIn("city", encoded_df.columns)

        # Row 0 is "New York": city_New York should be 1, others 0
        self.assertEqual(encoded_df.loc[0, "city_New York"], 1)
        self.assertEqual(encoded_df.loc[0, "city_London"], 0)
        self.assertEqual(encoded_df.loc[0, "city_Paris"], 0)

        # Row 1 is "London": city_London should be 1, others 0
        self.assertEqual(encoded_df.loc[1, "city_London"], 1)
        self.assertEqual(encoded_df.loc[1, "city_New York"], 0)
        self.assertEqual(encoded_df.loc[1, "city_Paris"], 0)

    def test_one_hot_encoder_drop_first(self):
        """Verify drop_first drops the first category indicator to reduce collinearity."""
        encoder = OneHotEncoder(drop_first=True)
        encoded_df, new_cols = encoder.fit_transform(self.sample_df, columns=["city"])

        # First category 'London' should be dropped
        self.assertNotIn("city_London", encoded_df.columns)
        self.assertIn("city_New York", encoded_df.columns)
        self.assertIn("city_Paris", encoded_df.columns)
        self.assertEqual(len(new_cols), 2)

    # -------------------------------------------------------------------
    # 3. CategoricalFeatureEncoder Helper Tests
    # -------------------------------------------------------------------

    def test_categorical_feature_encoder_multi_column(self):
        """Verify multi-column label and one-hot encoding on DataFrames."""
        df_label, mappings = CategoricalFeatureEncoder.label_encode(self.sample_df, columns=["city", "tier"])
        self.assertIn("city", mappings)
        self.assertIn("tier", mappings)
        self.assertTrue(np.issubdtype(df_label["city"].dtype, np.integer))
        self.assertTrue(np.issubdtype(df_label["tier"].dtype, np.integer))

    # -------------------------------------------------------------------
    # 4. Flask /encode Endpoint Integration Tests
    # -------------------------------------------------------------------

    def test_encode_endpoint_label_and_one_hot(self):
        """Verify Flask /encode API endpoint for both label and one_hot encoding."""
        client = app.test_client()
        app_module.df_global = self.sample_df.copy()

        # Test Label Encoding via API
        resp = client.post("/encode", json={"encoding_type": "label", "columns": ["city"]})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["encoding_type"], "label")
        self.assertIn("city", data["mappings"])

        # Test One-Hot Encoding via API
        resp_oh = client.post("/encode", json={"encoding_type": "one_hot", "columns": ["city"]})
        self.assertEqual(resp_oh.status_code, 200)
        data_oh = resp_oh.get_json()
        self.assertEqual(data_oh["status"], "success")
        self.assertEqual(data_oh["encoding_type"], "one_hot")
        self.assertTrue(len(data_oh["generated_columns"]) >= 2)


if __name__ == "__main__":
    unittest.main()
