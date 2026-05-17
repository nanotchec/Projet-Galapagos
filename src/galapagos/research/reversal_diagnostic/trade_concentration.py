import pandas as pd
import numpy as np

def run_trade_concentration_diagnostic(df: pd.DataFrame, selected_col: str = "rebuilt_selected") -> dict:
    """
    Check if losses are concentrated.
    """
    selected = df[df[selected_col]].copy()
    if selected.empty:
        return {"status": "NO_TRADES"}
        
    if not isinstance(selected.index, pd.DatetimeIndex):
        selected.index = pd.to_datetime(selected.index)
        
    outcome_col = "outcome_forward_return" if "outcome_forward_return" in df.columns else "outcome_target"
    
    recent = selected[selected.index >= "2026-01-01"]
    if recent.empty:
        return {"status": "SAMPLE_TOO_SMALL"}
        
    losses = recent[recent[outcome_col] < 0][outcome_col]
    if losses.empty:
        return {"status": "NO_LOSSES_IN_2026"}
        
    total_loss = losses.sum()
    top_10_losses = losses.sort_values().head(10).sum()
    top_20_losses = losses.sort_values().head(20).sum()
    
    top_10_share = top_10_losses / total_loss if total_loss != 0 else 0.0
    
    status = "LOSSES_DIFFUSE"
    if top_10_share > 0.5:
        status = "LOSSES_CONCENTRATED_IN_FEW_TRADES"
        
    return {
        "recent_loss_total": float(total_loss),
        "top_10_loss_share": float(top_10_share),
        "status": status
    }
