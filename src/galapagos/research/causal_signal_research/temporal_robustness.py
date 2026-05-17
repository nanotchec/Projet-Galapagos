from __future__ import annotations

from typing import Any
import pandas as pd

def analyze_temporal_robustness(
    selected_mask: pd.Series,
    selection_frame: pd.DataFrame,
    outcome_frame: pd.DataFrame,
    pnl_col: str
) -> dict[str, Any]:
    """Break down performance by semester with strict robustness rules."""
    
    selected_idx = selected_mask[selected_mask].index
    if len(selected_idx) == 0:
        return {"status": "NO_TRADES"}
        
    trades = selection_frame.loc[selected_idx].merge(
        outcome_frame[[pnl_col]], left_index=True, right_index=True, how="left"
    )
    
    trades["timestamp"] = pd.to_datetime(trades["timestamp"], utc=True)
    trades["semester"] = trades["timestamp"].dt.year.astype(str) + " H" + ((trades["timestamp"].dt.month - 1) // 6 + 1).astype(str)
    
    breakdown = {}
    semesters = sorted(trades["semester"].unique())
    
    for sem in semesters:
        group = trades[trades["semester"] == sem]
        valid_pnl = group[pnl_col].dropna()
        if not valid_pnl.empty:
            breakdown[sem] = {
                "selected_count": len(group),
                "net_mean_pnl": float(valid_pnl.mean()),
                "win_rate": float((valid_pnl > 0).mean())
            }
            
    # Robustness rules
    pos_semesters = sum(1 for s in breakdown.values() if s["net_mean_pnl"] > 0)
    neg_semesters = sum(1 for s in breakdown.values() if s["net_mean_pnl"] <= 0)
    total_semesters = len(breakdown)
    
    recent_sem = semesters[-1] if semesters else None
    recent_pnl = breakdown[recent_sem]["net_mean_pnl"] if recent_sem in breakdown else 0
    recent_count = breakdown[recent_sem]["selected_count"] if recent_sem in breakdown else 0
    
    status = "TEMPORAL_ROBUSTNESS_WEAK"
    recent_status = "OK"
    
    if recent_pnl < 0 and recent_count >= 20:
        status = "TEMPORAL_ROBUSTNESS_RECENT_WEAK"
        recent_status = "NEGATIVE_PNL"
    elif total_semesters >= 3 and pos_semesters >= 3:
        status = "TEMPORAL_ROBUSTNESS_PROMISING"
    elif total_semesters < 3:
        status = "SAMPLE_TOO_SMALL"
        
    return {
        "breakdown": breakdown,
        "positive_windows_count": pos_semesters,
        "negative_windows_count": neg_semesters,
        "recent_window_net_mean_pnl": float(recent_pnl),
        "recent_window_selected_count": recent_count,
        "recent_window_status": recent_status,
        "status": status
    }
