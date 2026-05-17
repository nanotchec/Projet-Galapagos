"""Logic for planning intrabar data coverage expansion."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def plan_coverage(
    predictions_path: str,
    intrabar_path: str | None = None,
    version: str = "v1.20"
) -> dict[str, Any]:
    """Calculate current coverage and plan extension."""
    if not Path(predictions_path).exists():
        return {"status": "error", "message": f"Predictions not found: {predictions_path}"}
    
    preds_df = pd.read_parquet(predictions_path)
    if "timestamp" not in preds_df.columns:
        # Some versions might use 'time' or index
        if preds_df.index.name == "timestamp":
            preds_df = preds_df.reset_index()
        elif "time" in preds_df.columns:
            preds_df = preds_df.rename(columns={"time": "timestamp"})

    preds_df["timestamp"] = pd.to_datetime(preds_df["timestamp"], utc=True)
    unique_signals = pd.Series(preds_df["timestamp"].unique()).sort_values().values
    
    sig_min = unique_signals[0]
    sig_max = unique_signals[-1]
    
    total_candidates = len(unique_signals)
    
    current_info = {}
    if intrabar_path and Path(intrabar_path).exists():
        ib_df = pd.read_parquet(intrabar_path)
        ib_df["timestamp"] = pd.to_datetime(ib_df["timestamp"], utc=True)
        ib_min = ib_df["timestamp"].min()
        ib_max = ib_df["timestamp"].max()
        
        # Simple overlap check: signals that fall within [ib_min, ib_max]
        # In reality, trade ledger needs 4h to 12bar after signal.
        # But for planning, we check signal timestamp existence.
        covered_signals = preds_df[
            (preds_df["timestamp"] >= ib_min) & 
            (preds_df["timestamp"] <= ib_max)
        ]["timestamp"].nunique()
        
        current_info = {
            "intrabar_min": ib_min.isoformat(),
            "intrabar_max": ib_max.isoformat(),
            "rows": len(ib_df),
            "days": (ib_max - ib_min).days,
            "covered_candidates": covered_signals,
            "evaluated_ratio": covered_signals / total_candidates if total_candidates > 0 else 0
        }
    else:
        current_info = {
            "intrabar_min": None,
            "intrabar_max": None,
            "rows": 0,
            "days": 0,
            "covered_candidates": 0,
            "evaluated_ratio": 0
        }

    # Planning extension
    # We want to cover as many unique signals as possible.
    # Most signals are likely recent.
    extension_plan = {
        "signal_range_min": pd.Timestamp(sig_min).isoformat(),
        "signal_range_max": pd.Timestamp(sig_max).isoformat(),
        "total_candidates": total_candidates,
        "targets": {
            "20%": int(total_candidates * 0.2),
            "50%": int(total_candidates * 0.5),
            "80%": int(total_candidates * 0.8)
        },
        "recommended_range": {
            "start": (pd.Timestamp(sig_max) - pd.Timedelta(days=180)).isoformat(),
            "end": pd.Timestamp(sig_max).isoformat()
        },
        "estimate_disk_mb": (total_candidates * 1.2 * 12 * 48) / 1024 # Very rough estimate for 5m
    }
    
    return {
        "version": version,
        "current_state": current_info,
        "plan": extension_plan,
        "status": (
            "INTRABAR_EXTENSION_FEASIBLE" 
            if current_info["evaluated_ratio"] < 0.8 
            else "INTRABAR_COVERAGE_SUFFICIENT"
        )
    }
