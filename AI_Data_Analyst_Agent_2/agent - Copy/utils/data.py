def apply_filters(df, filters):
    for col, val in filters.items():
        df = df[df[col] == val]
    return df

from utils.scaler import MinMaxScaler, min_max_scale_column
