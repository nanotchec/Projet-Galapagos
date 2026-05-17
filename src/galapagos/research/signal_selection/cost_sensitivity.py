from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_cost_sensitivity(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze how performance degrades with increasing costs."""
    if df.empty:
        return {}
        
    # Audit gross/net/cost consistency
    observed_gross_mean = float(df["gross_pnl_pct"].mean()) if "gross_pnl_pct" in df else 0.0
    observed_net_mean = float(df["net_pnl_pct"].mean()) if "net_pnl_pct" in df else 0.0
    observed_cost_mean = float(df["cost_pct"].mean()) if "cost_pct" in df else 0.0
    inferred_cost_mean = observed_gross_mean - observed_net_mean
    
    cols = ["gross_pnl_pct", "net_pnl_pct", "cost_pct"]
    cost_columns_available = all(c in df.columns for c in cols)
    
    diff_abs = abs(inferred_cost_mean - observed_cost_mean)
    if cost_columns_available and diff_abs < 1e-6:
        reconstruction_status = "COST_RECONSTRUCTION_OK"
    elif cost_columns_available:
        reconstruction_status = "COST_RECONSTRUCTION_AMBIGUOUS"
    else:
        reconstruction_status = "COST_ASSUMPTION_NEEDS_VALIDATION"

    costs_to_test = [0.0, 0.001, 0.002, 0.003, 0.005]
    sensitivity = {}
    
    for cost in costs_to_test:
        net_pnls = df["gross_pnl_pct"] - cost
        sensitivity[f"cost_{cost*100:.1f}%"] = {
            "mean_pnl": float(net_pnls.mean()),
            "total_pnl": float(net_pnls.sum()),
            "win_rate": float((net_pnls > 0).mean())
        }
        
    break_even = observed_gross_mean
    
    if reconstruction_status == "COST_RECONSTRUCTION_OK":
        if break_even > 0.005:
            verdict = "COST_ROBUST_EDGE_CANDIDATE"
        elif break_even > 0.003:
            verdict = "COST_SENSITIVE_EDGE"
        else:
            verdict = "EDGE_DISAPPEARS_AT_REALISTIC_COST"
    else:
        verdict = "COST_SENSITIVITY_PROMISING_BUT_NEEDS_COST_VALIDATION"
        
    return {
        "observed_gross_mean": observed_gross_mean,
        "observed_net_mean": observed_net_mean,
        "observed_cost_mean": observed_cost_mean,
        "inferred_cost_mean": inferred_cost_mean,
        "cost_columns_available": cost_columns_available,
        "cost_reconstruction_status": reconstruction_status,
        "sensitivity": sensitivity,
        "break_even_cost_pct": float(break_even * 100),
        "verdict": verdict
    }
