"""Categorical Feature Encoder Engine: Label & One-Hot Encoding (CR-856).

Provides deterministic categorical feature encoding for machine learning dataset preparation:
- LabelEncoder: maps distinct category string values to unique integer indices [0, N-1].
- OneHotEncoder: converts categorical variables into binary indicator columns (0 or 1).
- CategoricalFeatureEncoder: unified helper for DataFrame transformations.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


class LabelEncoder:
    """Encodes categorical text values to unique non-negative integer mappings."""

    def __init__(self):
        self.classes_: List[Any] = []
        self.mapping_: Dict[Any, int] = {}
        self.inverse_mapping_: Dict[int, Any] = {}

    def fit(self, values: Union[pd.Series, List[Any]]) -> "LabelEncoder":
        """Identifies distinct categories and creates sorted integer mappings."""
        if isinstance(values, pd.Series):
            distinct = values.dropna().unique().tolist()
        else:
            distinct = list(dict.fromkeys([v for v in values if pd.notna(v)]))

        # Sort categories for deterministic mapping
        try:
            self.classes_ = sorted(distinct)
        except TypeError:
            self.classes_ = sorted(distinct, key=str)

        self.mapping_ = {cat: idx for idx, cat in enumerate(self.classes_)}
        self.inverse_mapping_ = {idx: cat for cat, idx in self.mapping_.items()}
        return self

    def transform(
        self,
        values: Union[pd.Series, List[Any]],
        handle_unknown: str = "error",
    ) -> Union[pd.Series, List[int]]:
        """Maps categorical values to integers using the fitted mapping."""
        if not self.mapping_:
            raise ValueError("LabelEncoder is not fitted yet. Call fit() first.")

        is_series = isinstance(values, pd.Series)
        input_list = values.tolist() if is_series else list(values)
        encoded: List[int] = []

        for val in input_list:
            if pd.isna(val):
                encoded.append(-1)
            elif val in self.mapping_:
                encoded.append(self.mapping_[val])
            elif handle_unknown == "ignore":
                encoded.append(-1)
            else:
                raise ValueError(f"Unseen category '{val}' encountered during transform.")

        return pd.Series(encoded, index=values.index) if is_series else encoded

    def fit_transform(
        self,
        values: Union[pd.Series, List[Any]],
        handle_unknown: str = "error",
    ) -> Union[pd.Series, List[int]]:
        """Fits encoder and transforms values in a single step."""
        return self.fit(values).transform(values, handle_unknown=handle_unknown)

    def inverse_transform(self, encoded_values: Union[pd.Series, List[int]]) -> List[Any]:
        """Maps integer codes back to original category values."""
        is_series = isinstance(encoded_values, pd.Series)
        input_list = encoded_values.tolist() if is_series else list(encoded_values)
        return [self.inverse_mapping_.get(code, None) for code in input_list]


class OneHotEncoder:
    """Converts categorical variables into binary indicator vectors (0 or 1)."""

    def __init__(self, drop_first: bool = False, prefix_sep: str = "_"):
        self.drop_first = drop_first
        self.prefix_sep = prefix_sep
        self.categories_: Dict[str, List[Any]] = {}
        self.output_columns_: Dict[str, List[str]] = {}

    def fit(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> "OneHotEncoder":
        """Identifies distinct categories per target column."""
        if columns is None:
            columns = df.select_dtypes(include=["object", "category"]).columns.tolist()

        self.categories_ = {}
        self.output_columns_ = {}

        for col in columns:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' does not exist in DataFrame.")

            series = df[col].dropna()
            try:
                cats = sorted(series.unique().tolist())
            except TypeError:
                cats = sorted(series.unique().tolist(), key=str)

            self.categories_[col] = cats
            cats_to_encode = cats[1:] if self.drop_first and len(cats) > 1 else cats
            self.output_columns_[col] = [f"{col}{self.prefix_sep}{c}" for c in cats_to_encode]

        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforms DataFrame by generating binary indicator columns for categories."""
        if not self.categories_:
            raise ValueError("OneHotEncoder is not fitted yet. Call fit() first.")

        out_df = df.copy()

        for col, cats in self.categories_.items():
            cats_to_encode = cats[1:] if self.drop_first and len(cats) > 1 else cats

            for cat in cats_to_encode:
                col_name = f"{col}{self.prefix_sep}{cat}"
                out_df[col_name] = (out_df[col] == cat).astype(int)

            # Drop the original categorical column
            out_df.drop(columns=[col], inplace=True)

        return out_df

    def fit_transform(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Fits encoder and transforms DataFrame, returning new df and generated binary columns."""
        self.fit(df, columns=columns)
        transformed = self.transform(df)
        all_new_cols = [col for cols in self.output_columns_.values() for col in cols]
        return transformed, all_new_cols


class CategoricalFeatureEncoder:
    """Unified helper class providing label and one-hot encoding operations on DataFrames."""

    @classmethod
    def label_encode(
        cls,
        df: pd.DataFrame,
        columns: List[str],
    ) -> Tuple[pd.DataFrame, Dict[str, Dict[str, int]]]:
        """Label encodes designated columns into integers, returning transformed df and mappings."""
        out_df = df.copy()
        mappings = {}

        for col in columns:
            if col not in out_df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")
            encoder = LabelEncoder()
            out_df[col] = encoder.fit_transform(out_df[col])
            mappings[col] = encoder.mapping_

        return out_df, mappings

    @classmethod
    def one_hot_encode(
        cls,
        df: pd.DataFrame,
        columns: List[str],
        drop_first: bool = False,
        prefix_sep: str = "_",
    ) -> Tuple[pd.DataFrame, List[str]]:
        """One-hot encodes designated columns into binary indicators."""
        encoder = OneHotEncoder(drop_first=drop_first, prefix_sep=prefix_sep)
        return encoder.fit_transform(df, columns=columns)
