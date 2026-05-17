"""Decompose losses across microstructure regimes V1.49."""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any

def analyze_regime_losses(
    frame: pd.DataFrame,
    outcome_col: str = "target_4h_bin"
) -> dict[str, Any]:
    """Analyze which regimes contribute most to negative outcomes."""
    if outcome_col not in frame.columns:
        # Try to find an outcome column
        possible = ["target", "outcome", "forward_return", "target_4h_bin"]
        for p in possible:
            if p in frame.columns:
                outcome_col = p
                break
        else:
            return {"status": "MISSING_OUTCOME", "message": "No outcome column found for loss decomposition"}

    # We assume 'target_4h_bin' or similar is what we want
    # Let's say we look at rows where outcome is negative (if numeric) or 'loss' if categorical
    
    regimes = frame.groupby("micro_regime")
    
    loss_stats = {}
    for name, group in regimes:
        # If numeric, mean outcome
        if np.issubdtype(group[outcome_col].dtype, np.number):
            mean_ret = group[outcome_col].mean()
            std_ret = group[outcome_col].std()
            neg_ratio = (group[outcome_col] < 0).mean()
        else:
            # Categorical
            mean_ret = 0
            std_ret = 0
            neg_ratio = (group[outcome_col].astype(str).str.lower().str.contains("loss")).mean()
            
        loss_stats[str(name)] = {
            "mean_outcome": float(mean_ret),
            "std_outcome": float(std_ret),
            "negative_ratio": float(neg_ratio),
            "sample_size": len(group)
        }
        
    return {
        "outcome_col_used": outcome_col,
        "loss_by_regime": loss_stats,
        "most_lossy_regime": max(loss_stats, key=lambda k: loss_stats[k]["negative_ratio"]) if loss_stats else None
    }
