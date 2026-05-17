from __future__ import annotations

import pandas as pd
from typing import Any

def run_calibration_drift_diagnostic(
    mask: pd.Series, 
    selection_frame: pd.DataFrame, 
    outcome_frame: pd.DataFrame
) -> dict[str, Any]:
    """Analyze if probabilities are still calibrated recently."""
    
    selected_idx = mask[mask].index
    trades = selection_frame.loc[selected_idx].merge(
        outcome_frame, left_index=True, right_index=True, how="left"
    )
    
    trades["timestamp"] = pd.to_datetime(trades["timestamp"], utc=True)
    trades["semester"] = trades["timestamp"].dt.year.astype(str) + " H" + ((trades["timestamp"].dt.month - 1) // 6 + 1).astype(str)
    
    pnl_col = "net_pnl_pct" if "net_pnl_pct" in trades.columns else "forward_return_12bar"
    
    calibration = {}
    for sem, group in trades.groupby("semester"):
        avg_prob = float(group["predicted_probability"].mean()) if "predicted_probability" in group.columns else 0.0
        realized_wr = float((group[pnl_col] > 0).mean()) if pnl_col in group.columns else 0.0
        
        calibration[sem] = {
            "avg_predicted_probability": avg_prob,
            "realized_win_rate": realized_wr,
            "calibration_gap": realized_wr - avg_prob,
            "selected_count": len(group)
        }
        
    recent_sem = "2026 H1"
    recent_gap = calibration.get(recent_sem, {}).get("calibration_gap", 0.0)
    
    status = "CALIBRATION_STABLE"
    if recent_gap < -0.1: # 10% lower WR than predicted
        status = "CALIBRATION_DEGRADED_RECENTLY"
        
    return {
        "calibration_by_semester": calibration,
        "calibration_status": status,
        "calibration_proxy_only": True
    }
