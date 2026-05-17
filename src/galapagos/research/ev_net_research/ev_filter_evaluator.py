from __future__ import annotations

from typing import Any

import pandas as pd


def evaluate_ev_filters(
    df: pd.DataFrame, 
    filter_defs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Evaluate the performance of various EV filters.
    """
    results = []
    
    eligible_cols = [f["filter_name"] for f in filter_defs if f.get("eligible_for_ranking", True)]
    
    for col in eligible_cols:
        subset = df[df[col]]
        
        if len(subset) == 0:
            results.append({
                "filter_name": col,
                "selected_count": 0,
                "status": "NO_SIGNALS_SELECTED"
            })
            continue
            
        net_returns = subset["forward_return_12bar"] - subset["cost_proxy"]
        
        results.append({
            "filter_name": col,
            "selected_count": len(subset),
            "net_mean_pnl": float(net_returns.mean()),
            "net_median_pnl": float(net_returns.median()),
            "win_rate": float((subset["actual_target"] == 1).mean()),
            "profit_factor": float(
                subset[net_returns > 0]["forward_return_12bar"].sum() / 
                abs(subset[net_returns < 0]["forward_return_12bar"].sum())
            ) if len(subset[net_returns < 0]) > 0 else 0,
            "avg_ev_proxy": float(subset["ev_calibrated_proxy"].mean()),
            "status": "EVALUATED"
        })
        
    return results
