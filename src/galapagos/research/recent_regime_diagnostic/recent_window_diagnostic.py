from __future__ import annotations

import pandas as pd
from typing import Any

def run_recent_window_diagnostic(
    mask: pd.Series, 
    selection_frame: pd.DataFrame, 
    outcome_frame: pd.DataFrame
) -> dict[str, Any]:
    """Compare 2026 H1 metrics against history."""
    
    selected_idx = mask[mask].index
    trades = selection_frame.loc[selected_idx].merge(
        outcome_frame, left_index=True, right_index=True, how="left"
    )
    
    trades["timestamp"] = pd.to_datetime(trades["timestamp"], utc=True)
    trades["semester"] = trades["timestamp"].dt.year.astype(str) + " H" + ((trades["timestamp"].dt.month - 1) // 6 + 1).astype(str)
    
    pnl_col = "net_pnl_pct" if "net_pnl_pct" in trades.columns else "forward_return_12bar"
    gross_col = "gross_pnl_pct" if "gross_pnl_pct" in trades.columns else "forward_return_12bar"
    
    breakdown = {}
    semesters = sorted(trades["semester"].unique())
    
    for sem in semesters:
        group = trades[trades["semester"] == sem]
        valid_pnl = group[pnl_col].dropna()
        if not valid_pnl.empty:
            breakdown[sem] = {
                "selected_count": len(group),
                "net_mean_pnl": float(valid_pnl.mean()),
                "win_rate": float((valid_pnl > 0).mean()),
                "gross_mean_pnl": float(group[gross_col].mean()) if gross_col in group.columns else 0.0,
                "profit_factor": float(valid_pnl[valid_pnl > 0].sum() / abs(valid_pnl[valid_pnl < 0].sum())) if not valid_pnl[valid_pnl < 0].empty else 0.0
            }
            
    recent_sem = "2026 H1"
    recent_data = breakdown.get(recent_sem, {})
    historical_pnl = [v["net_mean_pnl"] for k, v in breakdown.items() if k != recent_sem]
    avg_hist_pnl = sum(historical_pnl) / len(historical_pnl) if historical_pnl else 0.0
    
    degradation_confirmed = False
    if recent_data and recent_data.get("net_mean_pnl", 0) < 0 and avg_hist_pnl > 0:
        degradation_confirmed = True
        
    return {
        "breakdown": breakdown,
        "recent_window": recent_sem,
        "recent_net_mean_pnl": recent_data.get("net_mean_pnl"),
        "historical_avg_pnl": avg_hist_pnl,
        "recent_vs_historical_delta": recent_data.get("net_mean_pnl", 0) - avg_hist_pnl,
        "recent_degradation_confirmed": degradation_confirmed,
        "status": "RECENT_DEGRADATION_CONFIRMED" if degradation_confirmed else "RECENT_WINDOW_STABLE"
    }
