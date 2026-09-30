from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


class MinMaxScaler:
    """Min-Max normalization engine scaling numerical column values to [0.0, 1.0]."""

    def __init__(self, feature_range: Tuple[float, float] = (0.0, 1.0)):
        self.feature_range = feature_range
        self.stats: Dict[str, Dict[str, float]] = {}

    def fit(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> "MinMaxScaler":
        """Computes min and max values for specified numerical columns."""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        self.stats = {}
        for col in columns:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' does not exist in DataFrame.")

            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if series.empty:
                col_min, col_max = 0.0, 0.0
            else:
                col_min = float(series.min())
                col_max = float(series.max())

            self.stats[col] = {
                "min": col_min,
                "max": col_max,
                "range": col_max - col_min,
            }
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies min-max normalization formula (val - min) / (max - min)."""
        if not self.stats:
            raise ValueError("Scaler has not been fitted yet. Call fit() first.")

        scaled_df = df.copy()
        for col, stat in self.stats.items():
            col_min = stat["min"]
            col_max = stat["max"]
            diff = col_max - col_min

            if diff == 0:
                scaled_df[col] = self.feature_range[0]
            else:
                series = pd.to_numeric(scaled_df[col], errors="coerce")
                scaled = (series - col_min) / diff
                if self.feature_range != (0.0, 1.0):
                    scaled = scaled * (self.feature_range[1] - self.feature_range[0]) + self.feature_range[0]
                scaled_df[col] = scaled

        return scaled_df

    def fit_transform(
        self, df: pd.DataFrame, columns: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
        """Fits scaler and transforms dataframe, returning scaled DataFrame and computed stats."""
        self.fit(df, columns)
        return self.transform(df), self.stats


def min_max_scale_column(
    values: Union[List[Union[int, float]], pd.Series],
    col_min: Optional[float] = None,
    col_max: Optional[float] = None,
) -> List[Optional[float]]:
    """Scales a 1D list or series of numerical values to [0.0, 1.0]."""
    numeric_vals = [float(v) for v in values if v is not None and not pd.isna(v)]
    if not numeric_vals:
        return []

    c_min = float(min(numeric_vals)) if col_min is None else float(col_min)
    c_max = float(max(numeric_vals)) if col_max is None else float(col_max)
    diff = c_max - c_min

    if diff == 0:
        return [0.0 for _ in values]

    return [(float(v) - c_min) / diff if (v is not None and not pd.isna(v)) else None for v in values]
