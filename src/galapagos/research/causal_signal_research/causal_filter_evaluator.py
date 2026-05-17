from __future__ import annotations

from typing import Any
import pandas as pd

def evaluate_filter_performance(
    filter_mask: pd.Series, 
    selection_frame: pd.DataFrame,
    outcome_frame: pd.DataFrame
) -> dict[str, Any]:
    """
    Evaluate a filter mask against outcomes.
    Ensures that selection_frame was used for filtering, not outcome_frame.
    """
    selected_idx = filter_mask[filter_mask].index
    if len(selected_idx) == 0:
        return {"selected_count": 0, "status": "NO_TRADES"}
        
    # Join selection metadata with outcomes
    selected_trades = selection_frame.loc[selected_idx].merge(
        outcome_frame, left_index=True, right_index=True, how="left"
    )
    
    # Map possible outcome columns
    pnl_col = "mean_net_pnl_after_cost_pct"
    found_valid = pnl_col in selected_trades.columns and not selected_trades[pnl_col].dropna().empty
    
    if not found_valid:
        fallbacks = ["cost_adjusted_forward_return", "net_pnl_pct", "forward_return_12bar"]
        for col in fallbacks:
            if col in selected_trades.columns and not selected_trades[col].dropna().empty:
                pnl_col = col
                found_valid = True
                break
                
    if not found_valid:
        # If still not found, we cannot evaluate PnL
        pass

    metrics = {
        "selected_count": len(selected_trades),
        "status": "EXPLORATORY_ONLY"
    }
    
    if pnl_col in selected_trades.columns:
        valid_pnl = selected_trades[pnl_col].dropna()
        if not valid_pnl.empty:
            metrics["net_mean_pnl"] = float(valid_pnl.mean())
            metrics["net_median_pnl"] = float(valid_pnl.median())
            metrics["win_rate"] = float((valid_pnl > 0).mean())
            metrics["total_net_pnl"] = float(valid_pnl.sum())
            
            pos_sum = valid_pnl[valid_pnl > 0].sum()
            neg_sum = abs(valid_pnl[valid_pnl < 0].sum())
            metrics["profit_factor"] = float(pos_sum / neg_sum) if neg_sum > 0 else float('inf')
            
    return metrics
