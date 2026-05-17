from __future__ import annotations

import pandas as pd
from typing import Any

def load_diagnostic_data(preds_path: str, dataset_path: str | None = None) -> pd.DataFrame:
    """Load and prepare data for diagnostic."""
    df = pd.read_parquet(preds_path)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        
    return df

def separate_frames(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Strictly separate selection and outcome frames to prevent causal leakage."""
    
    # Comprehensive list of forbidden future-looking columns
    forbidden_cols = [
        "forward_return", "forward_return_6bar", "forward_return_12bar", 
        "cost_adjusted_forward_return", "net_pnl_pct", "gross_pnl_pct", 
        "mfe_pct", "mae_pct", "exit_reason", "simulation_status",
        "actual_target", "future", "target_future", "outcome"
    ]
    
    # Selection frame: strictly causal
    selection_cols = [c for c in df.columns if not any(f in c.lower() for f in forbidden_cols)]
    # Ensure timestamp is preserved in selection
    if "timestamp" not in selection_cols and "timestamp" in df.columns:
        selection_cols.append("timestamp")
        
    # Outcome frame: future data
    outcome_cols = [c for c in df.columns if any(f in c.lower() for f in forbidden_cols)]
    # We do NOT add timestamp to outcome_cols to avoid suffixes during merge
    
    return df[selection_cols].copy(), df[outcome_cols].copy()
