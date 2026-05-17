from __future__ import annotations

import pandas as pd


def estimate_causal_payoffs(
    df: pd.DataFrame, 
    lookback_bars: int = 1000
) -> pd.DataFrame:
    """
    Estimate average win and loss sizes using only past data.
    """
    df = df.sort_values("timestamp")
    
    # We use a rolling mean of past returns for successful/failed signals
    # Warning: this is a simplification for V1.32.
    # In a real system, we'd use a more sophisticated model.
    
    # We need a column for the actual outcome size if we want to estimate it.
    # Assuming 'forward_return_12bar' is available.
    
    # For now, let's use a fixed lookback or expanding window.
    # We only consider rows where actual_target is known (past).
    
    # We will compute the average return when target was 1 and when it was 0 in the past.
    
    # Logic to compute rolling causal estimates if returns are present
    if "forward_return_12bar" in df.columns:
        wins = df["forward_return_12bar"].where(df["actual_target"] == 1)
        losses = df["forward_return_12bar"].where(df["actual_target"] == 0)
        
        df["avg_win_past"] = wins.shift(1).expanding(min_periods=100).mean()
        df["avg_loss_past"] = losses.shift(1).expanding(min_periods=100).mean()
        
    df["payoff_estimate_ready"] = df["avg_win_past"].notna() & df["avg_loss_past"].notna()
    
    return df
