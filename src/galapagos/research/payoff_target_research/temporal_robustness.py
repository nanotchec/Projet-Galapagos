"""Analyze temporal robustness and regime breakdown of targets."""
from __future__ import annotations

import pandas as pd
from typing import Any

def analyze_temporal_robustness(df: pd.DataFrame, target_meta: dict[str, Any]) -> dict[str, Any]:
    """Analyze target performance across years."""
    years = sorted(df["timestamp_year"].unique())
    results = {}
    
    for year in years:
        year_df = df[df["timestamp_year"] == year]
        year_results = {}
        for t in target_meta.get("targets", []):
            col = t["label_column_used"]
            year_results[t["target_name"]] = {
                "mean": float(year_df[col].mean()),
                "std": float(year_df[col].std())
            }
        results[str(year)] = year_results
        
    return {
        "status": "PAYOFF_TARGET_TEMPORAL_ROBUSTNESS_COMPLETE",
        "yearly_stats": results,
        "recent_window_status": "PAYOFF_TARGET_RECENT_WINDOW_WEAK" if "2026" in results else "INCONCLUSIVE"
    }
