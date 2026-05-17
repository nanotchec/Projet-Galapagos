from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_regime_calibration(
    selection_frame: pd.DataFrame,
    outcome_frame: pd.DataFrame,
    target_col: str = "actual_target",
    prob_col: str = "predicted_probability",
    regime_col: str = "macro_regime"
) -> list[dict[str, Any]]:
    """
    Analyze calibration per market regime.
    """
    if regime_col not in selection_frame.columns:
        return [
            {"status": "REGIME_DIVERSITY_INSUFFICIENT", "error": f"Column {regime_col} missing"}
        ]
        
    df = selection_frame[[regime_col, prob_col]].copy()
    df[target_col] = outcome_frame[target_col]
    
    if "forward_return_12bar" in outcome_frame.columns:
        df["outcome"] = outcome_frame["forward_return_12bar"]
    else:
        df["outcome"] = 0.0
        
    regimes = df[regime_col].dropna().unique()
    
    results = []
    for regime in regimes:
        reg_df = df[df[regime_col] == regime]
        
        if len(reg_df) < 50:
            results.append({
                "regime": str(regime),
                "sample_count": len(reg_df),
                "status": "SAMPLE_TOO_SMALL"
            })
            continue
            
        avg_prob = reg_df[prob_col].mean()
        win_rate = reg_df[target_col].mean()
        gap = win_rate - avg_prob
        avg_outcome = reg_df["outcome"].mean()
        
        results.append({
            "regime": str(regime),
            "sample_count": len(reg_df),
            "avg_predicted_probability": float(avg_prob),
            "realized_win_rate": float(win_rate),
            "calibration_gap": float(gap),
            "avg_outcome": float(avg_outcome),
            "status": "REGIME_CALIBRATION_AVAILABLE"
        })
        
    if not results:
        return [{"status": "REGIME_DIVERSITY_INSUFFICIENT"}]
        
    return results
