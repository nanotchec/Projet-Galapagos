from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any

def run_regime_dependency_diagnostic(
    mask: pd.Series, 
    selection_frame: pd.DataFrame, 
    outcome_frame: pd.DataFrame,
    regime_definition_status: str = "REGIME_DEFINITION_OK"
) -> dict[str, Any]:
    """Diagnose if filter is overly dependent on bull regimes with prudent status."""
    
    selected_idx = mask[mask].index
    # We use selection_frame directly if mask was built on it
    trades = selection_frame.loc[selected_idx].merge(
        outcome_frame, left_index=True, right_index=True, how="left"
    )
    
    if "trend_regime" not in trades.columns:
        trades["trend_proxy"] = np.where(trades["predicted_probability"] >= 0.6, "bull_strength", "neutral")
    else:
        trades["trend_proxy"] = trades["trend_regime"]
        
    pnl_col = "net_pnl_pct" if "net_pnl_pct" in trades.columns else "forward_return_12bar"
    
    regime_metrics = {}
    total_trades = len(trades)
    
    for regime, group in trades.groupby("trend_proxy"):
        regime_metrics[str(regime)] = {
            "selected_count": len(group),
            "share": float(len(group) / total_trades),
            "net_mean_pnl": float(group[pnl_col].mean()) if pnl_col in group.columns else 0.0,
            "win_rate": float((group[pnl_col] > 0).mean()) if pnl_col in group.columns else 0.0
        }
        
    dominant_regime = None
    dominant_share = 0.0
    for r, m in regime_metrics.items():
        if m["share"] > dominant_share:
            dominant_share = m["share"]
            dominant_regime = r
            
    status = "REGIME_ROBUSTNESS_NOT_PROVEN"
    if dominant_share > 0.8:
        if regime_definition_status == "REGIME_DEFINITION_TOO_COARSE":
             status = "APPARENT_BULL_DEPENDENCY_WITH_COARSE_REGIME_DEFINITION"
        else:
             status = "BULL_REGIME_DEPENDENT"
             
    return {
        "regime_metrics": regime_metrics,
        "dominant_regime": dominant_regime,
        "dominant_regime_share": dominant_share,
        "regime_dependency_status": status,
        "regime_diversity_insufficient": True if len(regime_metrics) < 2 else False
    }
