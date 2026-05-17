from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_stability(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze whether performance depends on few trades or periods."""
    if df.empty:
        return {}
        
    total_net = df["net_pnl_pct"].sum()
    if total_net == 0:
        return {"verdict": "STABILITY_INCONCLUSIVE"}
        
    # Concentration by month
    df["month"] = df["timestamp"].dt.to_period("M")
    monthly_pnl = df.groupby("month")["net_pnl_pct"].sum()
    
    top_month_contribution = monthly_pnl.max() / total_net if total_net > 0 else 0
    
    # Concentration by trades
    sorted_trades = df.sort_values("net_pnl_pct", ascending=False)
    top_10_sum = sorted_trades.head(10)["net_pnl_pct"].sum()
    top_10_contribution = float(top_10_sum / total_net) if total_net > 0 else 0.0
    top_month_contribution = float(monthly_pnl.max() / total_net) if total_net > 0 else 0.0
    
    warning = False
    verdict = "PERFORMANCE_DISTRIBUTED"
    if top_10_contribution > 0.50:
        verdict = "PERFORMANCE_CONCENTRATED"
        warning = True
        
    return {
        "top_month_contribution": top_month_contribution,
        "top_10_trades_contribution": top_10_contribution,
        "monthly_pnl": {str(k): float(v) for k, v in monthly_pnl.items()},
        "performance_concentration_warning": warning,
        "verdict": verdict
    }
