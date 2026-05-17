from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_tail_risk(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze the impact of extreme losers with unambiguous naming."""
    if df.empty:
        return {}
        
    total_net_pnl_pct = df["net_pnl_pct"].sum()
    negative_trades = df[df["net_pnl_pct"] < 0]
    total_negative_pnl_pct = negative_trades["net_pnl_pct"].sum()
    
    if total_negative_pnl_pct == 0:
        return {
            "total_net_pnl_pct": total_net_pnl_pct,
            "total_negative_pnl_pct": 0.0,
            "top_1pct_loss_contribution_to_negative_pnl": 0.0,
            "top_5pct_loss_contribution_to_negative_pnl": 0.0,
            "worst_trade_pnl_pct": df["net_pnl_pct"].min(),
            "verdict": "NO_NEGATIVE_TRADES"
        }
        
    # Sort by loss (most negative first)
    sorted_losers = negative_trades.sort_values("net_pnl_pct")
    
    top_1pct_count = max(1, int(len(df) * 0.01))
    top_5pct_count = max(1, int(len(df) * 0.05))
    
    top_1pct_loss_sum = sorted_losers.head(top_1pct_count)["net_pnl_pct"].sum()
    top_5pct_loss_sum = sorted_losers.head(top_5pct_count)["net_pnl_pct"].sum()
    
    # We compare against the total negative PnL to see if losses are concentrated in the tail
    top_1pct_contribution = (
        top_1pct_loss_sum / total_negative_pnl_pct if total_negative_pnl_pct != 0 else 0
    )
    
    verdict = "LOSSES_DIFFUSE"
    if top_1pct_contribution > 0.2: # 1% of trades account for >20% of negative PnL
        verdict = "LOSSES_CONCENTRATED_IN_TAIL"
        
    return {
        "total_net_pnl_pct": total_net_pnl_pct,
        "total_negative_pnl_pct": total_negative_pnl_pct,
        "top_1pct_loss_contribution_to_negative_pnl": top_1pct_contribution,
        "top_5pct_loss_contribution_to_negative_pnl": (
            top_5pct_loss_sum / total_negative_pnl_pct if total_negative_pnl_pct != 0 else 0
        ),
        "worst_trade_pnl_pct": df["net_pnl_pct"].min(),
        "verdict": verdict
    }
