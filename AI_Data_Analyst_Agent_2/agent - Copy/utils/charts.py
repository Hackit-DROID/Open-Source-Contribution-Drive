import pandas as pd


def generate_charts(df):
    num_cols = df.select_dtypes(include='number').columns

    if len(num_cols) == 0:
        return {}

    col = num_cols[0]

    return {
        "bar": {
            "labels": df.index.astype(str).tolist()[:10],
            "data": df[col].tolist()[:10]
        },
        "line": {
            "labels": df.index.astype(str).tolist()[:10],
            "data": df[col].tolist()[:10]
        },
        "pie": {
            "labels": df.index.astype(str).tolist()[:5],
            "data": df[col].tolist()[:5]
        },
        "heatmap": {
            "labels": list(num_cols),
            "data": df[num_cols].corr().iloc[0].tolist()
        }
    }