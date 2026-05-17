from __future__ import annotations

import pandas as pd
from typing import Any

def run_cost_drag_diagnostic(
    mask: pd.Series, 
    selection_frame: pd.DataFrame, 
    outcome_frame: pd.DataFrame
) -> dict[str, Any]:
    """Assess if costs are killing the recent edge with honest reporting."""
    
    selected_idx = mask[mask].index
    trades = selection_frame.loc[selected_idx].merge(
        outcome_frame, left_index=True, right_index=True, how="left"
    )
    
    trades["timestamp"] = pd.to_datetime(trades["timestamp"], utc=True)
    trades["semester"] = trades["timestamp"].dt.year.astype(str) + " H" + ((trades["timestamp"].dt.month - 1) // 6 + 1).astype(str)
    
    net_col = "net_pnl_pct" if "net_pnl_pct" in trades.columns else "forward_return_12bar"
    gross_col = "gross_pnl_pct" if "gross_pnl_pct" in trades.columns else None
    
    cost_breakdown = {}
    total_cost_drag = 0.0
    measurable = True if gross_col else False
    
    for sem, group in trades.groupby("semester"):
        net = group[net_col].dropna()
        if gross_col:
            gross = group[gross_col].dropna()
            cost_drag = gross.mean() - net.mean()
            total_cost_drag += cost_drag
            killed = bool(gross.mean() > 0 and net.mean() <= 0)
        else:
            gross = net # Fallback
            cost_drag = 0.0
            killed = False
            
        cost_breakdown[sem] = {
            "gross_mean_pnl": float(gross.mean()),
            "net_mean_pnl": float(net.mean()),
            "estimated_cost_drag": float(cost_drag),
            "killed_by_costs": killed
        }
        
    recent_sem = "2026 H1"
    recent = cost_breakdown.get(recent_sem, {})
    
    if not measurable:
        status = "COST_DRAG_NOT_ISOLATED_IN_CURRENT_OUTCOME_PROXY"
    elif recent.get("killed_by_costs"):
        status = "EDGE_KILLED_BY_COSTS_RECENT"
    elif recent.get("gross_mean_pnl", 0) < 0:
        status = "EDGE_NEGATIVE_BEFORE_COSTS"
    else:
        status = "COSTS_NOT_PRIMARY_RECENT"
        
    return {
        "cost_breakdown_by_semester": cost_breakdown,
        "cost_drag_status": status,
        "cost_drag_measurable": measurable,
        "cost_columns_available": [gross_col] if gross_col else [],
        "outcome_may_already_be_net": True if not gross_col else False
    }
