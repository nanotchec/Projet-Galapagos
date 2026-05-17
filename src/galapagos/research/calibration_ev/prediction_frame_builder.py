from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.research.calibration_ev.point_in_time_audit import audit_point_in_time_features


def build_prediction_frames(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """
    Build strictly separated selection and outcome frames.
    """
    # 1. Initial raw audit
    raw_audit = audit_point_in_time_features(df)
    
    selection_cols = raw_audit["metadata_columns"] + raw_audit["allowed_feature_columns"]
    # We allow unknown columns in selection for now but they triggered a warning in audit
    selection_cols += raw_audit["unknown_columns"]
    
    outcome_cols = raw_audit["forbidden_outcome_columns"]
    
    # Ensure timestamp is in both for joining if needed later
    if "timestamp" not in outcome_cols and "timestamp" in df.columns:
        outcome_cols = ["timestamp"] + outcome_cols
        
    selection_frame = df[selection_cols].copy()
    outcome_frame = df[outcome_cols].copy()
    
    # 2. Hardened selection audit (re-verify the built frame)
    selection_audit = audit_point_in_time_features(selection_frame, selection_cols=selection_cols)
    
    integrity_status = "PREDICTION_FRAME_INTEGRITY_PASSED"
    leaks = selection_audit["selection_frame_forbidden_columns"]
    
    if leaks:
        integrity_status = "PREDICTION_FRAME_INTEGRITY_FAILED_SELECTION_LEAKAGE"
        
    integrity_report = {
        "raw_rows": len(df),
        "unique_timestamps": df["timestamp"].nunique() if "timestamp" in df.columns else 0,
        "selection_columns": selection_cols,
        "outcome_columns": outcome_cols,
        "forbidden_columns_in_selection": leaks,
        "filters_received_outcomes": False,
        "selection_frame_status": selection_audit["point_in_time_status"],
        "outcome_frame_status": "OUTCOME_FRAME_AVAILABLE",
        "integrity_status": integrity_status
    }
    
    return selection_frame, outcome_frame, integrity_report
