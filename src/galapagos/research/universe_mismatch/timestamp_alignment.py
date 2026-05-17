import pandas as pd

def analyze_timestamp_alignment(df_preds: pd.DataFrame, df_dataset: pd.DataFrame):
    # Check naive vs aware
    preds_naive = df_preds.index.tz is None
    dataset_naive = df_dataset.index.tz is None
    
    unique_preds = df_preds.index.unique()
    unique_dataset = df_dataset.index.unique()
    
    intersection = unique_preds.intersection(unique_dataset)
    
    # Rows per timestamp
    counts_per_ts = df_preds.index.value_counts()
    
    return {
        "predictions_rows": len(df_preds),
        "predictions_unique_timestamps": len(unique_preds),
        "dataset_rows": len(df_dataset),
        "dataset_unique_timestamps": len(unique_dataset),
        "intersection_count": len(intersection),
        "preds_tz_naive": preds_naive,
        "dataset_tz_naive": dataset_naive,
        "duplicate_rows_per_timestamp_mean": float(counts_per_ts.mean()),
        "duplicate_rows_per_timestamp_max": int(counts_per_ts.max()),
        "unmatched_prediction_timestamps": len(unique_preds) - len(intersection),
        "unmatched_dataset_timestamps": len(unique_dataset) - len(intersection),
        "timestamp_alignment_status": "TIMESTAMP_ALIGNMENT_OK" if len(intersection) > 0 else "TIMESTAMP_ALIGNMENT_FAIL"
    }
