from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_policy_performance(df: pd.DataFrame, policy_name: str) -> dict[str, Any]:
    """Calculate detailed metrics for a single policy."""
    if df.empty:
        return {}
        
    wins = df[df["net_pnl_pct"] > 0]
    losses = df[df["net_pnl_pct"] < 0]
    
    # Cost Flip: winning gross, losing net
    cost_flips = df[(df["gross_pnl_pct"] > 0) & (df["net_pnl_pct"] <= 0)]
    
    total_gross = df["gross_pnl_pct"].sum()
    total_net = df["net_pnl_pct"].sum()
    total_cost = total_gross - total_net
    
    # Best/Worst 5%
    n_5pct = max(1, int(len(df) * 0.05))
    sorted_pnl = df["net_pnl_pct"].sort_values()
    worst_5pct = sorted_pnl.head(n_5pct).mean()
    best_5pct = sorted_pnl.tail(n_5pct).mean()

    verdict = "POLICY_FAILS_AFTER_COSTS"
    if total_gross <= 0:
        verdict = "POLICY_FAILS_BEFORE_COSTS"
    elif total_net > 0:
        verdict = "POLICY_HAS_NET_EDGE" # Unlikely in V1.23
        
    return {
        "policy": policy_name,
        "trades_count": len(df),
        "win_rate": len(wins) / len(df),
        "gross_mean_pnl_pct": df["gross_pnl_pct"].mean(),
        "net_mean_pnl_pct": df["net_pnl_pct"].mean(),
        "net_median_pnl_pct": df["net_pnl_pct"].median(),
        "total_gross_pnl_pct": total_gross,
        "total_cost_pct": total_cost,
        "total_net_pnl_pct": total_net,
        "profit_factor": abs(wins["net_pnl_pct"].sum() / losses["net_pnl_pct"].sum()) if not losses.empty else float('inf'),
        "average_win": wins["net_pnl_pct"].mean() if not wins.empty else 0,
        "average_loss": losses["net_pnl_pct"].mean() if not losses.empty else 0,
        "cost_flip_count": len(cost_flips),
        "worst_5pct_mean": worst_5pct,
        "best_5pct_mean": best_5pct,
        "verdict": verdict
    }
