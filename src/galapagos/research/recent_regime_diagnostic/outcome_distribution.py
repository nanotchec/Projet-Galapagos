from __future__ import annotations

import pandas as pd
from typing import Any

def run_outcome_distribution_diagnostic(
    mask: pd.Series, 
    selection_frame: pd.DataFrame, 
    outcome_frame: pd.DataFrame
) -> dict[str, Any]:
    """Analyze outcome tails and skew."""
    
    selected_idx = mask[mask].index
    trades = selection_frame.loc[selected_idx].merge(
        outcome_frame, left_index=True, right_index=True, how="left"
    )
    
    trades["timestamp"] = pd.to_datetime(trades["timestamp"], utc=True)
    trades["semester"] = trades["timestamp"].dt.year.astype(str) + " H" + ((trades["timestamp"].dt.month - 1) // 6 + 1).astype(str)
    
    pnl_col = "net_pnl_pct" if "net_pnl_pct" in trades.columns else "forward_return_12bar"
    
    dist_stats = {}
    for sem, group in trades.groupby("semester"):
        pnl = group[pnl_col].dropna()
        dist_stats[sem] = {
            "mean": float(pnl.mean()),
            "std": float(pnl.std()),
            "p10": float(pnl.quantile(0.1)),
            "p25": float(pnl.quantile(0.25)),
            "p75": float(pnl.quantile(0.75)),
            "p90": float(pnl.quantile(0.9)),
            "skew": float(pnl.skew())
        }
        
    recent_sem = "2026 H1"
    recent_p10 = dist_stats.get(recent_sem, {}).get("p10", 0.0)
    hist_p10s = [v["p10"] for k, v in dist_stats.items() if k != recent_sem]
    avg_hist_p10 = sum(hist_p10s) / len(hist_p10s) if hist_p10s else 0.0
    
    status = "OUTCOME_DISTRIBUTION_STABLE"
    if recent_p10 < avg_hist_p10 - 0.01: # 1% worse left tail
        status = "RECENT_LEFT_TAIL_WORSENED"
        
    return {
        "outcome_stats_by_semester": dist_stats,
        "outcome_distribution_status": status
    }
