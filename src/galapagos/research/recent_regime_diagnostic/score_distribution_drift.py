from __future__ import annotations

import pandas as pd
from typing import Any

def run_score_distribution_drift(
    selection_frame: pd.DataFrame
) -> dict[str, Any]:
    """Check if the distribution of predicted probabilities has shifted recently."""
    
    if "predicted_probability" not in selection_frame.columns:
        return {"status": "COLUMN_MISSING"}
        
    df = selection_frame.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["semester"] = df["timestamp"].dt.year.astype(str) + " H" + ((df["timestamp"].dt.month - 1) // 6 + 1).astype(str)
    
    dist_breakdown = {}
    for sem, group in df.groupby("semester"):
        probs = group["predicted_probability"]
        dist_breakdown[sem] = {
            "mean": float(probs.mean()),
            "median": float(probs.median()),
            "p75": float(probs.quantile(0.75)),
            "p90": float(probs.quantile(0.90)),
            "p95": float(probs.quantile(0.95)),
            "share_above_0_65": float((probs >= 0.65).mean())
        }
        
    recent_sem = "2026 H1"
    recent_share = dist_breakdown.get(recent_sem, {}).get("share_above_0_65", 0.0)
    hist_shares = [v["share_above_0_65"] for k, v in dist_breakdown.items() if k != recent_sem]
    avg_hist_share = sum(hist_shares) / len(hist_shares) if hist_shares else 0.0
    
    status = "SCORE_DISTRIBUTION_STABLE"
    if recent_share < avg_hist_share * 0.7:
        status = "SCORE_SELECTION_RATE_WEAKENED_RECENTLY"
    elif abs(recent_share - avg_hist_share) / (avg_hist_share + 1e-6) > 0.3:
        status = "SCORE_DISTRIBUTION_SHIFT_DETECTED"
        
    return {
        "distribution_by_semester": dist_breakdown,
        "score_distribution_status": status,
        "recent_selection_rate": recent_share,
        "historical_avg_selection_rate": avg_hist_share
    }
