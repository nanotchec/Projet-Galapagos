from __future__ import annotations

from typing import Any
import pandas as pd
import numpy as np

def audit_signal_dedup(df: pd.DataFrame) -> dict[str, Any]:
    """Audit the dataframe for multiple signals at the same timestamp with robustness checks."""
    total_rows = len(df)
    unique_ts = df["timestamp"].nunique()
    
    counts = df.groupby("timestamp").size()
    max_per_ts = int(counts.max()) if not counts.empty else 0
    mean_per_ts = float(counts.mean()) if not counts.empty else 0
    dup_rows = int((counts[counts > 1]).sum()) if not counts.empty else 0
    
    # Identify potential cause of duplicates
    cols = ["model_name", "target", "split_name"]
    present_cols = [c for c in cols if c in df.columns]
    
    available_models = []
    per_model_counts = {}
    if "model_name" in df.columns:
        available_models = list(df["model_name"].unique())
        per_model_counts = df["model_name"].value_counts().to_dict()
        
    excluded_models = []
    if "model_name" in df.columns:
         excluded_models = ["dummy_most_frequent"] if "dummy_most_frequent" in available_models else []

    status = "DEDUP_AUDIT_COMPLETE"
    robustness_status = "STABLE"
    
    if dup_rows > 0:
        robustness_status = "ORDER_DEPENDENT_WITHOUT_PRIORITY"

    return {
        "raw_prediction_rows": total_rows,
        "unique_timestamps": unique_ts,
        "rows_per_timestamp_mean": mean_per_ts,
        "rows_per_timestamp_max": max_per_ts,
        "duplicate_timestamp_rows": dup_rows,
        "columns_checked": present_cols,
        "available_models": available_models,
        "per_model_counts": per_model_counts,
        "excluded_models": excluded_models,
        "model_filtering_applied": len(excluded_models) > 0,
        "default_policy_order_dependency": True if dup_rows > 0 else False,
        "dedup_robustness_status": robustness_status,
        "status": status
    }

def apply_dedup_policy(df: pd.DataFrame, policy: str = "first_stable_per_timestamp") -> pd.DataFrame:
    """
    Apply a strict de-duplication policy.
    """
    work = df.copy()
    
    # Avoid dummy models by default
    if "model_name" in work.columns:
        work = work[work["model_name"] != "dummy_most_frequent"].copy()
        
    if policy == "first_stable_per_timestamp":
        # Neutral policy: sort by timestamp and keep first encounter
        ordered = work.sort_values(["timestamp"])
        deduped = ordered.groupby("timestamp", group_keys=False).head(1)
        return deduped
        
    elif policy == "explicit_model_policy":
        if "model_name" in work.columns:
             # Prioritize hist_gradient_boosting
             work["_model_priority"] = np.where(work["model_name"] == "hist_gradient_boosting", 0, 1)
             ordered = work.sort_values(["timestamp", "_model_priority"])
             deduped = ordered.groupby("timestamp", group_keys=False).head(1)
             return deduped
        else:
             return apply_dedup_policy(df, "first_stable_per_timestamp")
             
    else:
        raise ValueError(f"Unknown dedup policy: {policy}")
