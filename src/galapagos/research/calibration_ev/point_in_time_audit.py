from typing import Any

import pandas as pd


def audit_point_in_time_features(
    df: pd.DataFrame, 
    selection_cols: list[str] | None = None
) -> dict[str, Any]:
    """
    Audit columns available and classify them to ensure point-in-time integrity.
    Distinguishes between the raw dataset and the actual selection frame.
    """
    columns = df.columns.tolist()
    
    forbidden_keywords = [
        "forward_return", "net_pnl", "gross_pnl", "exit_reason", 
        "future", "actual_target", "outcome", "pnl", "mfe", "mae",
        "target_future", "target_label"
    ]
    
    metadata_keywords = [
        "timestamp", "model_name", "feature_set", "target", "split_name",
        "id", "symbol", "timeframe"
    ]
    
    allowed_feature_keywords = [
        "predicted_probability", "predicted_label", "score", "feature",
        "ohlcv", "macro", "derivatives", "combined"
    ]
    
    forbidden_found = []
    metadata_found = []
    allowed_features = []
    unknown_cols = []
    
    for col in columns:
        col_lower = col.lower()
        if any(k in col_lower for k in forbidden_keywords):
            forbidden_found.append(col)
        elif any(k in col_lower for k in metadata_keywords):
            metadata_found.append(col)
        elif any(k in col_lower for k in allowed_feature_keywords):
            allowed_features.append(col)
        else:
            unknown_cols.append(col)
            
    # Audit selection frame if provided
    selection_forbidden = []
    if selection_cols:
        selection_forbidden = [c for c in selection_cols if c in forbidden_found]
        
    status = "POINT_IN_TIME_AUDIT_PASSED"
    warning = None
    
    if selection_forbidden:
        status = "POINT_IN_TIME_AUDIT_FAILED_SELECTION_LEAKAGE"
    elif forbidden_found:
        status = "POINT_IN_TIME_AUDIT_PASSED_WITH_CLASSIFIED_OUTCOMES"
        warning = (
            f"Raw dataset contains {len(forbidden_found)} outcome columns, "
            "but they are excluded from selection."
        )
    elif unknown_cols:
        status = "POINT_IN_TIME_AUDIT_HAS_UNKNOWN_COLUMNS"
        
    return {
        "total_columns": len(columns),
        "allowed_feature_columns": allowed_features,
        "metadata_columns": metadata_found,
        "forbidden_outcome_columns": forbidden_found,
        "diagnostic_only_columns": forbidden_found,  # Alias for V1.30.2
        "unknown_columns": unknown_cols,
        "raw_dataset_contains_outcomes": len(forbidden_found) > 0,
        "raw_dataset_outcomes_classified": True,
        "selection_frame_forbidden_columns": selection_forbidden,
        "point_in_time_status": status,
        "point_in_time_warning": warning
    }
