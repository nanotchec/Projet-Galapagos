from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_cost_impact(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze how costs affect the bottom line."""
    if df.empty:
        return {}
        
    gross_pnl = df["gross_pnl_pct"].mean()
    net_pnl = df["net_pnl_pct"].mean()
    avg_cost = gross_pnl - net_pnl
    
    # Sensitivity
    scenarios = {
        "current_cost": net_pnl,
        "half_cost": gross_pnl - (avg_cost * 0.5),
        "zero_cost": gross_pnl,
        "double_cost": gross_pnl - (avg_cost * 2.0)
    }
    
    # Break-even cost
    # net = gross - cost => cost = gross for net=0
    breakeven_cost = gross_pnl
    
    verdict = "COSTS_SECONDARY_LOSS_DRIVER"
    if gross_pnl <= 0:
        verdict = "NO_GROSS_EDGE"
    elif net_pnl < 0 and gross_pnl > 0:
        verdict = "COSTS_PRIMARY_LOSS_DRIVER"
        
    return {
        "avg_gross_pnl_pct": gross_pnl,
        "avg_net_pnl_pct": net_pnl,
        "avg_cost_per_trade_pct": avg_cost,
        "cost_to_gross_ratio": avg_cost / abs(gross_pnl) if gross_pnl != 0 else float('inf'),
        "sensitivity_scenarios": scenarios,
        "breakeven_cost_pct": breakeven_cost,
        "verdict": verdict
    }
