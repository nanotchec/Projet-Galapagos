from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_exit_reasons(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze PnL contribution by exit reason for a specific policy."""
    if df.empty:
        return {}
        
    stats = df.groupby("exit_reason").agg({
        "net_pnl_pct": ["count", "mean", "sum"],
        "gross_pnl_pct": ["mean"]
    })
    
    # Flatten columns
    stats.columns = [f"{c[0]}_{c[1]}" for c in stats.columns]
    
    reasons_dict = stats.to_dict(orient="index")
    
    # Identify primary loser reason
    primary_loser_reason = str(stats["net_pnl_pct_sum"].idxmin())
    
    total_net_pnl = df["net_pnl_pct"].sum()
    
    verdict = "EXIT_POLICY_NOT_PRIMARY_DRIVER"
    
    if "stop_loss" in reasons_dict:
        sl_sum = reasons_dict["stop_loss"]["net_pnl_pct_sum"]
        if sl_sum < 0 and (total_net_pnl == 0 or sl_sum / total_net_pnl > 0.6):
            verdict = "STOP_LOSS_DOMINATES_LOSSES"
            
    if "take_profit" in reasons_dict:
        tp_count = reasons_dict["take_profit"]["net_pnl_pct_count"]
        if tp_count < len(df) * 0.05:
            verdict = "TAKE_PROFIT_TOO_RARE"
            
    if primary_loser_reason == "horizon_timeout" and len(reasons_dict) == 1:
        verdict = "HORIZON_ONLY_BEST_BUT_STILL_NEGATIVE"

    return {
        "reasons": reasons_dict,
        "primary_loser_reason": primary_loser_reason,
        "verdict": verdict
    }
