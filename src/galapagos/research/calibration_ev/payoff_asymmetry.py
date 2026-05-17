from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_payoff_asymmetry(
    selection_frame: pd.DataFrame,
    outcome_frame: pd.DataFrame,
    target_col: str = "actual_target",
    prob_col: str = "predicted_probability",
    cost_proxy: float = 0.0010  # 10 bps default
) -> list[dict[str, Any]]:
    """
    Analyze payoff asymmetry (win vs loss size) per probability bin.
    """
    df = selection_frame[[prob_col]].copy()
    df[target_col] = outcome_frame[target_col]
    
    if "forward_return_12bar" in outcome_frame.columns:
        df["outcome"] = outcome_frame["forward_return_12bar"]
    else:
        df["outcome"] = 0.0
        
    bins = [0.50, 0.60, 0.70, 0.80, 1.00]
    labels = [f"[{bins[i]:.2f}, {bins[i+1]:.2f})" for i in range(len(bins)-1)]
    df["bin"] = pd.cut(df[prob_col], bins=bins, labels=labels, right=False)
    
    results = []
    for label in labels:
        bin_df = df[df["bin"] == label]
        if len(bin_df) == 0:
            continue
            
        wins = bin_df[bin_df["outcome"] > 0]["outcome"]
        losses = bin_df[bin_df["outcome"] < 0]["outcome"]
        
        avg_win = wins.mean() if len(wins) > 0 else 0.0
        avg_loss_abs = abs(losses.mean()) if len(losses) > 0 else 0.0
        win_rate = bin_df[target_col].mean()
        
        # Payoff ratio
        payoff = avg_win / avg_loss_abs if avg_loss_abs > 0 else 0.0
        
        # Breakeven WR = 1 / (1 + payoff)
        be_wr = 1 / (1 + payoff) if payoff > 0 else 1.0
        
        # After costs (rough estimate)
        avg_win_net = avg_win - cost_proxy
        avg_loss_net = avg_loss_abs + cost_proxy
        payoff_net = avg_win_net / avg_loss_net if avg_loss_net > 0 else 0.0
        be_wr_net = 1 / (1 + payoff_net) if payoff_net > 0 else 1.0
        
        verdict = "PAYOFF_ASYMMETRY_FAVORABLE" if payoff > 1.2 else "PAYOFF_ASYMMETRY_UNFAVORABLE"
        
        results.append({
            "bin": label,
            "avg_win": float(avg_win),
            "avg_loss_abs": float(avg_loss_abs),
            "win_loss_ratio": float(payoff),
            "realized_win_rate": float(win_rate),
            "breakeven_win_rate_before_costs": float(be_wr),
            "breakeven_win_rate_after_costs": float(be_wr_net),
            "payoff_asymmetry_status": verdict
        })
        
    return results
