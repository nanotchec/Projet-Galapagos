from __future__ import annotations

from typing import Any

import pandas as pd


def audit_walk_forward_leakage(
    train_df: pd.DataFrame, 
    test_df: pd.DataFrame,
    input_cols: list[str]
) -> dict[str, Any]:
    """
    Audit for temporal leakage in walk-forward calibration.
    """
    train_ts = pd.to_datetime(train_df["timestamp"])
    test_ts = pd.to_datetime(test_df["timestamp"])
    
    overlap = train_ts.max() >= test_ts.min()
    
    forbidden_keywords = ["forward_return", "net_pnl", "actual_target"]
    leaks = [c for c in input_cols if any(k in c.lower() for k in forbidden_keywords)]
    
    status = "WALK_FORWARD_CALIBRATION_NO_LEAKAGE_DETECTED"
    if overlap:
        status = "WALK_FORWARD_CALIBRATION_TEMPORAL_OVERLAP_DETECTED"
    elif leaks:
        status = "WALK_FORWARD_CALIBRATION_FORBIDDEN_COLUMNS_DETECTED"
        
    return {
        "train_end": train_ts.max().isoformat(),
        "test_start": test_ts.min().isoformat(),
        "temporal_overlap": overlap,
        "input_columns": input_cols,
        "forbidden_columns_in_input": leaks,
        "leakage_status": status
    }
