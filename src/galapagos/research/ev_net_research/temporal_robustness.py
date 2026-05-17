from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_temporal_robustness(
    df: pd.DataFrame, 
    filter_defs: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Analyze filter performance across temporal windows.
    """
    eligible_cols = [f["filter_name"] for f in filter_defs if f.get("eligible_for_ranking", True)]
    filter_cols = eligible_cols
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Define windows
    windows = {
        "2024_H1": ("2024-01-01", "2024-07-01"),
        "2024_H2": ("2024-07-01", "2025-01-01"),
        "2025_H1": ("2025-01-01", "2025-07-01"),
        "2025_H2": ("2025-07-01", "2026-01-01"),
        "2026_H1": ("2026-01-01", "2026-07-01")
    }
    
    temporal_results = []
    summary_by_filter = {}
    
    for col in filter_cols:
        summary_by_filter[col] = {
            "active_windows_count": 0,
            "inactive_windows_count": 0,
            "recent_2026_selected_count": 0,
            "recent_2026_pnl": 0.0,
            "activity_status": "UNKNOWN"
        }
    
    for win_name, (start, end) in windows.items():
        win_df = df[(df["timestamp"] >= start) & (df["timestamp"] < end)]
        
        for col in filter_cols:
            if len(win_df) == 0:
                temporal_results.append({
                    "window": win_name, 
                    "filter_name": col, 
                    "selected_count": 0, 
                    "net_mean_pnl": 0, 
                    "status": "NO_DATA"
                })
                summary_by_filter[col]["inactive_windows_count"] += 1
                continue
                
            subset = win_df[win_df[col]]
            count = len(subset)
            pnl = float(
                (subset["forward_return_12bar"] - subset["cost_proxy"]).mean()
            ) if count > 0 else 0
            
            temporal_results.append({
                "window": win_name,
                "filter_name": col,
                "selected_count": count,
                "net_mean_pnl": pnl,
                "status": "TEMPORAL_EVALUATED" if count > 0 else "NO_SIGNALS"
            })
            
            if count > 0:
                summary_by_filter[col]["active_windows_count"] += 1
                if win_name == "2026_H1":
                    summary_by_filter[col]["recent_2026_selected_count"] = count
                    summary_by_filter[col]["recent_2026_pnl"] = pnl
            else:
                summary_by_filter[col]["inactive_windows_count"] += 1

    # Determine status
    for col in filter_cols:
        s = summary_by_filter[col]
        if s["active_windows_count"] == 0:
            s["activity_status"] = "INACTIVE_ALL_PERIODS"
        elif (s["active_windows_count"] == 1 and 
              "2024_H1" in [t["window"] for t in temporal_results 
                           if t["filter_name"] == col and t["selected_count"] > 0]):
             s["activity_status"] = "TEMPORAL_ACTIVITY_COLLAPSE"
        elif s["recent_2026_selected_count"] == 0:
             s["activity_status"] = "RECENT_WINDOW_NO_SIGNALS"
        else:
             s["activity_status"] = "TEMPORALLY_ACTIVE"

    return {
        "temporal_results": temporal_results,
        "summary_by_filter": summary_by_filter
    }
