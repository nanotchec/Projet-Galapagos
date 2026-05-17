import pandas as pd
import numpy as np

def run_cost_drag_diagnostic(df: pd.DataFrame, selected_col: str = "rebuilt_selected") -> dict:
    """
    Analyze impact of costs on recent reversal.
    """
    selected = df[df[selected_col]].copy()
    if selected.empty:
        return {"status": "NO_TRADES"}
        
    if not isinstance(selected.index, pd.DatetimeIndex):
        selected.index = pd.to_datetime(selected.index)
        
    outcome_col = "outcome_forward_return" if "outcome_forward_return" in df.columns else "outcome_target"
    
    # We might not have 'gross' outcome, but we have 'cost_proxy'
    # Outcome is usually net.
    if "cost_proxy" not in selected.columns:
        return {"status": "COST_DRAG_NOT_ISOLATED"}
        
    def get_cost_stats(sub_df):
        if sub_df.empty: return None
        avg_cost = sub_df["cost_proxy"].mean()
        avg_net = sub_df[outcome_col].mean()
        avg_gross = avg_net + avg_cost
        
        return {
            "avg_cost_proxy": float(avg_cost),
            "avg_net_outcome": float(avg_net),
            "avg_gross_outcome": float(avg_gross),
            "cost_drag_ratio": float(avg_cost / abs(avg_gross)) if avg_gross != 0 else 0.0
        }
        
    history = selected[selected.index < "2026-01-01"]
    recent = selected[selected.index >= "2026-01-01"]
    
    history_stats = get_cost_stats(history)
    recent_stats = get_cost_stats(recent)
    
    status = "COST_DIAGNOSTIC_INCONCLUSIVE"
    if history_stats and recent_stats:
        if recent_stats["avg_gross_outcome"] < 0:
            status = "EDGE_NEGATIVE_BEFORE_COSTS"
        elif recent_stats["cost_drag_ratio"] > history_stats["cost_drag_ratio"] * 1.5:
            status = "COST_DRAG_EXPLAINS_REVERSAL"
            
    return {
        "history_costs": history_stats,
        "recent_costs": recent_stats,
        "status": status
    }
