from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_regime_robustness(
    df: pd.DataFrame, 
    filter_defs: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Analyze filter performance across market regimes.
    """
    eligible_cols = [f["filter_name"] for f in filter_defs if f.get("eligible_for_ranking", True)]
    filter_cols = eligible_cols
    # Assuming 'macro_regime' or 'derivatives_risk_regime' is available
    regime_col = "macro_regime" if "macro_regime" in df.columns else None
    
    if not regime_col:
        return {
            "regime_status": "REGIME_ANALYSIS_LIMITED_COARSE_DEFINITION",
            "results": []
        }
        
    regime_results = []
    regimes = df[regime_col].unique()
    
    for r in regimes:
        reg_df = df[df[regime_col] == r]
        
        for col in filter_cols:
            subset = reg_df[reg_df[col]]
            count = len(subset)
            pnl = float(
                (subset["forward_return_12bar"] - subset["cost_proxy"]).mean()
            ) if count > 0 else 0
            
            regime_results.append({
                "regime": r,
                "filter_name": col,
                "selected_count": count,
                "net_mean_pnl": pnl
            })
            
    return {
        "regime_status": "REGIME_ANALYSIS_COMPLETED",
        "results": regime_results
    }
