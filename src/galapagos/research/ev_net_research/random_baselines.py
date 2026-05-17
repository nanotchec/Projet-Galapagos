from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def generate_random_baselines(
    df: pd.DataFrame, 
    observed_results: list[dict[str, Any]], 
    filter_defs: list[dict[str, Any]] = None,
    iterations: int = 100
) -> list[dict[str, Any]]:
    """
    Generate random baselines for each filter.
    """
    baseline_results = []
    
    eligible_names = None
    if filter_defs:
        eligible_names = [
            f["filter_name"] for f in filter_defs 
            if f.get("eligible_for_ranking", True)
        ]
    
    # Ensure timestamp is datetime
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["month_key"] = df["timestamp"].dt.strftime("%Y-%m")
    
    # Pre-calculate returns
    full_returns = df["forward_return_12bar"] - df["cost_proxy"]
    
    for res in observed_results:
        filter_name = res["filter_name"]
        if eligible_names is not None and filter_name not in eligible_names:
            continue
            
        count = res["selected_count"]
        if count == 0:
            continue
            
        # 1. Global Same-Count
        global_means = []
        for _ in range(iterations):
            random_idx = np.random.choice(df.index, count, replace=False)
            global_means.append(full_returns.loc[random_idx].mean())
            
        baseline_results.append({
            "filter_name": filter_name,
            "baseline_type": "GLOBAL_SAME_COUNT",
            "observed_net_mean_pnl": res["net_mean_pnl"],
            "random_p50": float(np.percentile(global_means, 50)),
            "random_p95": float(np.percentile(global_means, 95)),
            "beats_random_p95": res["net_mean_pnl"] > np.percentile(global_means, 95),
            "baseline_status": "COMPLETED"
        })
        
        # 2. Monthly-Count Preserving
        # Count trades per month for this filter
        month_counts = df[df[filter_name]].groupby("month_key").size()
        
        monthly_means = []
        for _ in range(iterations):
            sampled_indices = []
            for month, m_count in month_counts.items():
                month_indices = df[df["month_key"] == month].index
                if len(month_indices) >= m_count:
                    sampled_indices.extend(np.random.choice(month_indices, m_count, replace=False))
                else:
                    sampled_indices.extend(month_indices)
            
            if sampled_indices:
                monthly_means.append(full_returns.loc[sampled_indices].mean())
        
        if monthly_means:
            p95 = np.percentile(monthly_means, 95)
            baseline_results.append({
                "filter_name": filter_name,
                "baseline_type": "MONTHLY_COUNT_PRESERVING",
                "observed_net_mean_pnl": res["net_mean_pnl"],
                "random_p50": float(np.percentile(monthly_means, 50)),
                "random_p95": float(p95),
                "beats_random_p95": res["net_mean_pnl"] > p95,
                "baseline_status": "COMPLETED"
            })
            
    return baseline_results
