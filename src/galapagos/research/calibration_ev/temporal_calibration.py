from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.research.calibration_ev.calibration_metrics import calculate_calibration_metrics


def analyze_temporal_calibration(
    selection_frame: pd.DataFrame,
    outcome_frame: pd.DataFrame,
    target_col: str = "actual_target",
    prob_col: str = "predicted_probability"
) -> list[dict[str, Any]]:
    """
    Analyze calibration drift over time.
    """
    df = selection_frame[["timestamp", prob_col]].copy()
    df[target_col] = outcome_frame[target_col]
    
    if "forward_return_12bar" in outcome_frame.columns:
        df["outcome"] = outcome_frame["forward_return_12bar"]
    else:
        df["outcome"] = 0.0
        
    windows = [
        ("2024 H1", "2024-01-01", "2024-06-30"),
        ("2024 H2", "2024-07-01", "2024-12-31"),
        ("2025 H1", "2025-01-01", "2025-06-30"),
        ("2025 H2", "2025-07-01", "2025-12-31"),
        ("2026 H1", "2026-01-01", "2026-06-30")
    ]
    
    results = []
    for name, start, end in windows:
        mask = (df["timestamp"] >= start) & (df["timestamp"] <= end)
        win_df = df[mask]
        
        if len(win_df) < 50:
            results.append({
                "window": name,
                "sample_count": len(win_df),
                "status": "SAMPLE_TOO_SMALL"
            })
            continue
            
        metrics = calculate_calibration_metrics(
            win_df[target_col].values,
            win_df[prob_col].values
        )
        
        avg_prob = win_df[prob_col].mean()
        win_rate = win_df[target_col].mean()
        gap = win_rate - avg_prob
        avg_net_outcome = win_df["outcome"].mean()
        
        verdict = "CALIBRATION_STABLE"
        if metrics.get("ece", 0) > 0.15:
            verdict = "CALIBRATION_DRIFT_RECENT"
        if gap < -0.1:
            verdict = "CALIBRATION_RECENT_OVERCONFIDENCE"
            
        results.append({
            "window": name,
            "sample_count": len(win_df),
            "avg_predicted_probability": float(avg_prob),
            "realized_win_rate": float(win_rate),
            "brier": metrics.get("brier_score"),
            "ece": metrics.get("ece"),
            "avg_net_outcome": float(avg_net_outcome),
            "calibration_gap": float(gap),
            "status": verdict
        })
        
    return results
