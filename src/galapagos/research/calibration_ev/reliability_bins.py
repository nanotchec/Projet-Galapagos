from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_reliability_bins(
    selection_frame: pd.DataFrame, 
    outcome_frame: pd.DataFrame,
    target_col: str = "actual_target",
    prob_col: str = "predicted_probability"
) -> list[dict[str, Any]]:
    """
    Analyze reliability and performance per probability bin.
    """
    df = selection_frame[[prob_col]].copy()
    df[target_col] = outcome_frame[target_col]
    
    if "forward_return_12bar" in outcome_frame.columns:
        df["outcome"] = outcome_frame["forward_return_12bar"]
    else:
        df["outcome"] = 0.0
        
    bins = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 1.00]
    labels = [f"[{bins[i]:.2f}, {bins[i+1]:.2f})" for i in range(len(bins)-1)]
    
    df["bin"] = pd.cut(df[prob_col], bins=bins, labels=labels, right=False)
    
    results = []
    for label in labels:
        bin_df = df[df["bin"] == label]
        if len(bin_df) == 0:
            results.append({"bin": label, "sample_count": 0, "status": "SAMPLE_TOO_SMALL"})
            continue
            
        avg_prob = bin_df[prob_col].mean()
        win_rate = bin_df[target_col].mean()
        gap = win_rate - avg_prob
        avg_outcome = bin_df["outcome"].mean()
        
        wins = bin_df[bin_df["outcome"] > 0]["outcome"]
        losses = bin_df[bin_df["outcome"] < 0]["outcome"]
        
        avg_win = wins.mean() if len(wins) > 0 else 0.0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0.0
        payoff = avg_win / avg_loss if avg_loss > 0 else 0.0
        
        results.append({
            "bin": label,
            "sample_count": len(bin_df),
            "avg_predicted_probability": float(avg_prob),
            "realized_win_rate": float(win_rate),
            "calibration_gap": float(gap),
            "avg_forward_return": float(avg_outcome),
            "avg_win": float(avg_win),
            "avg_loss": float(avg_loss),
            "payoff_ratio": float(payoff),
            "status": "DATA_AVAILABLE"
        })
        
    return results
