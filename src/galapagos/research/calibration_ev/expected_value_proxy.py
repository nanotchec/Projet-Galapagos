from __future__ import annotations

from typing import Any

import pandas as pd


def calculate_ev_proxy(
    selection_frame: pd.DataFrame,
    outcome_frame: pd.DataFrame,
    prob_col: str = "predicted_probability",
    cost_proxy: float = 0.0010
) -> list[dict[str, Any]]:
    """
    Construct an EV proxy diagnostic per probability bin.
    """
    df = selection_frame[[prob_col]].copy()
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
            continue
            
        avg_prob = bin_df[prob_col].mean()
        
        wins = bin_df[bin_df["outcome"] > 0]["outcome"]
        losses = bin_df[bin_df["outcome"] < 0]["outcome"]
        
        avg_win = wins.mean() if len(wins) > 0 else 0.0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0.0
        
        # EV = p * Win - (1-p) * Loss - Costs
        ev_proxy = (avg_prob * avg_win) - ((1 - avg_prob) * avg_loss) - cost_proxy
        actual_avg_outcome = bin_df["outcome"].mean()
        
        results.append({
            "bin": label,
            "ev_proxy": float(ev_proxy),
            "actual_avg_outcome": float(actual_avg_outcome),
            "ev_vs_actual_gap": float(actual_avg_outcome - ev_proxy),
            "avg_win_conditional": float(avg_win),
            "avg_loss_conditional": float(avg_loss),
            "cost_proxy_used": cost_proxy,
            "ev_proxy_diagnostic_only": True,
            "uses_uncalibrated_probability": True,
            "status": "EV_PROXY_DIAGNOSTIC_ONLY"
        })
        
    return results
