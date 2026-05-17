from __future__ import annotations

from typing import Any
import pandas as pd
import numpy as np

def analyze_regime_breakdown(
    selected_mask: pd.Series,
    selection_frame: pd.DataFrame,
    outcome_frame: pd.DataFrame,
    pnl_col: str
) -> dict[str, Any]:
    """Break down performance by causal regime proxies with diversity audit."""
    
    selected_idx = selected_mask[selected_mask].index
    if len(selected_idx) == 0:
        return {"status": "NO_TRADES"}
        
    trades = selection_frame.loc[selected_idx].merge(
        outcome_frame[[pnl_col]], left_index=True, right_index=True, how="left"
    )
    
    # Build simple causal regimes if not present
    if "trend_regime" not in trades.columns:
        trades["trend_proxy"] = np.where(trades["predicted_probability"] >= 0.6, "bull_strength", "neutral")
    else:
        trades["trend_proxy"] = trades["trend_regime"]
        
    breakdown = {}
    total_selected = len(trades)
    
    for regime, group in trades.groupby("trend_proxy"):
        valid_pnl = group[pnl_col].dropna()
        if not valid_pnl.empty:
            breakdown[str(regime)] = {
                "selected_count": len(group),
                "share": float(len(group) / total_selected),
                "net_mean_pnl": float(valid_pnl.mean()),
                "win_rate": float((valid_pnl > 0).mean())
            }
            
    # Diversity audit
    regime_count = len(breakdown)
    dominant_regime = None
    dominant_share = 0.0
    
    for r, data in breakdown.items():
        if data["share"] > dominant_share:
            dominant_share = data["share"]
            dominant_regime = r
            
    status = "REGIME_BREAKDOWN_COMPLETE"
    diversity_status = "OK"
    
    if dominant_share > 0.80:
        status = "REGIME_BREAKDOWN_SINGLE_REGIME_DOMINANT"
        diversity_status = "DOMINANCE_DETECTED"
    elif sum(1 for r in breakdown.values() if r["selected_count"] >= 30) < 2:
        status = "REGIME_BREAKDOWN_INSUFFICIENT_DIVERSITY"
        diversity_status = "LOW_DIVERSITY"
        
    return {
        "breakdown": breakdown,
        "regime_count": regime_count,
        "dominant_regime": dominant_regime,
        "dominant_regime_share": dominant_share,
        "regime_diversity_status": diversity_status,
        "status": status
    }
