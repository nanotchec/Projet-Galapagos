import pandas as pd
from .universe_schema import FORBIDDEN_SELECTION_COLUMNS

def audit_inputs(df_preds, df_dataset):
    issues = []
    
    # Analysis
    pred_rows = len(df_preds)
    pred_ts = df_preds.index.nunique() if isinstance(df_preds.index, pd.DatetimeIndex) else df_preds["timestamp"].nunique()
    
    dataset_rows = len(df_dataset)
    dataset_ts = df_dataset.index.nunique() if isinstance(df_dataset.index, pd.DatetimeIndex) else df_dataset["timestamp"].nunique()
    
    # Required columns
    required_preds = ["predicted_probability"]
    missing_preds = [c for c in required_preds if c not in df_preds.columns]
    if missing_preds:
        issues.append(f"Missing required prediction columns: {missing_preds}")
        
    # Forbidden columns in raw
    found_forbidden = [c for c in FORBIDDEN_SELECTION_COLUMNS if c in df_preds.columns]
    
    status = "CANONICAL_INPUT_AUDIT_PASSED"
    if issues or found_forbidden:
        status = "CANONICAL_INPUT_AUDIT_WARNINGS"
        
    return {
        "predictions_rows": pred_rows,
        "predictions_unique_timestamps": pred_ts,
        "dataset_rows": dataset_rows,
        "dataset_unique_timestamps": dataset_ts,
        "required_columns_present": not missing_preds,
        "forbidden_columns_detected_in_raw": found_forbidden,
        "input_audit_status": status,
        "issues": issues
    }
