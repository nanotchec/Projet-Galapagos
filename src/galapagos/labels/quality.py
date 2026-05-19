from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any, Dict, List

from galapagos.labels.schemas import LABEL_COLUMNS_V2_6, FORBIDDEN_COLUMNS_V2_6
from galapagos.labels.registry import HORIZONS


def assess_label_quality(
    label_df: pd.DataFrame,
    expected_rows: int,
) -> Dict[str, Any]:
    """Evaluates the structural and temporal quality of a label DataFrame.
    
    Returns all parameters needed for the manifest and JSON report quality fields.
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    rows = len(label_df)
    
    # 1. Row counts & duplicates
    duplicate_rows = int(label_df.duplicated(subset=["event_ts"]).sum())
    tail_rows = int(label_df["tail_row"].sum())
    
    # 2. Counts by horizon
    valid_counts_by_horizon = {}
    for h in HORIZONS:
        valid_counts_by_horizon[f"h{h}"] = int(label_df[f"label_valid_h{h}"].sum())
        
    # 3. Null counts by column
    null_counts_by_column = {}
    for col in LABEL_COLUMNS_V2_6:
        null_counts = label_df[col].isna().sum()
        # count None as well for objects
        if label_df[col].dtype == object:
            null_counts = int((label_df[col].isna() | label_df[col].isnull() | (label_df[col] == "None") | (label_df[col] == "")).sum())
        else:
            null_counts = int(null_counts)
        null_counts_by_column[col] = null_counts
        
    # 4. Forbidden columns check
    forbidden_columns_present = False
    for col in label_df.columns:
        for term in FORBIDDEN_COLUMNS_V2_6:
            if term in col.lower():
                forbidden_columns_present = True
                errors.append(f"Forbidden column detected in labels dataset: {col}")
                
    # 5. Timestamps check
    timestamps_utc = True
    for ts_col in ["event_ts", "close_ts", "available_ts", "decision_ts"]:
        if ts_col in label_df.columns:
            ts = pd.to_datetime(label_df[ts_col])
            # Check if all end with Z or are UTC
            if not all(label_df[ts_col].astype(str).str.endswith("Z") | label_df[ts_col].astype(str).str.contains(r"\+00:00")):
                timestamps_utc = False
                errors.append(f"Timestamp column {ts_col} contains non-UTC formats")
                
    # 6. Monotonicity of event_ts
    monotonic_event_ts = bool(pd.to_datetime(label_df["event_ts"]).is_monotonic_increasing)
    if not monotonic_event_ts:
        errors.append("event_ts series is not strictly monotonic increasing")
        
    # 7. Causal separation guard: label_available_ts > decision_ts for all valid labels
    # If a label is valid (at least h1 is valid), available_ts must be > decision_ts
    causal_separation_guard_passed = True
    valid_labels_mask = label_df["label_valid_h1"]
    
    if valid_labels_mask.any():
        valid_rows = label_df[valid_labels_mask]
        avail = pd.to_datetime(valid_rows["label_available_ts"])
        dec = pd.to_datetime(valid_rows["decision_ts"])
        
        leakage = avail <= dec
        if leakage.any():
            causal_separation_guard_passed = False
            leak_indices = np.where(leakage)[0]
            errors.append(f"Causal separation guard failed: leakage detected on {len(leak_indices)} rows where label_available_ts <= decision_ts")
            
    # 8. Check that label_valid_h is false if future_close_h is null or label_end_ts_h is null
    label_available_ts_valid = True
    label_end_ts_valid = True
    
    for h in HORIZONS:
        invalid_validity_mask = label_df[f"label_valid_h{h}"] & (label_df[f"future_close_h{h}"].isna() | label_df[f"label_end_ts_h{h}"].isna())
        if invalid_validity_mask.any():
            label_available_ts_valid = False
            errors.append(f"Horizon h{h} marked as valid on rows with missing future close or label end timestamp")
            
    # Check that for all rows where label_valid_h is false, future features are nullified
    for h in HORIZONS:
        invalid_rows = label_df[~label_df[f"label_valid_h{h}"]]
        if not invalid_rows[f"future_close_h{h}"].isna().all():
            label_end_ts_valid = False
            errors.append(f"Horizon h{h} is invalid but future_close is not null")
            
    # Check that tail_row count matches expected count (the last 5 rows of the dataset)
    # h5 is invalid for the last 5 rows, h3 for the last 3 rows, h1 for the last row
    expected_tail_rows = 5
    if tail_rows != expected_tail_rows and rows >= expected_tail_rows:
        warnings.append(f"Unexpected tail rows count: got {tail_rows}, expected {expected_tail_rows}")
        
    return {
        "rows": rows,
        "expected_rows": expected_rows,
        "duplicate_rows": duplicate_rows,
        "tail_rows": tail_rows,
        "valid_counts_by_horizon": valid_counts_by_horizon,
        "null_counts_by_column": null_counts_by_column,
        "forbidden_columns_present": forbidden_columns_present,
        "timestamps_utc": timestamps_utc,
        "monotonic_event_ts": monotonic_event_ts,
        "label_available_ts_valid": label_available_ts_valid,
        "label_end_ts_valid": label_end_ts_valid,
        "causal_separation_guard_passed": causal_separation_guard_passed,
        "errors": errors,
        "warnings": warnings,
    }
