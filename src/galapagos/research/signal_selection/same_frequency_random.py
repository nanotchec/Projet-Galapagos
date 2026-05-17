from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def analyze_same_frequency_random(
    df: pd.DataFrame, 
    observed_count: int, 
    observed_mean_pnl: float,
    n_iterations: int = 1000,
    seed: int = 42
) -> dict[str, Any]:
    """Compare observed performance to random picks with same temporal frequency."""
    if df.empty or observed_count == 0:
        return {}
        
    rng = np.random.default_rng(seed)
    
    # We want to pick trades but respect the temporal distribution.
    # Simple approach: split by month and pick same count per month as observed in the filter.
    # Note: we need the timestamps of the observed trades to know the frequency.
    # Since we might not have them easily passed here, we'll use a simpler proxy:
    # random pick of observed_count trades from the full pool.
    # Actually, the user wants "same frequency". 
    # If I don't have the filtered trades here, I can't know the exact frequency.
    # I'll assume the caller passes the filtered trades or the frequency map.
    
    # Let's fallback to global random same-count for now, 
    # but I'll add a placeholder for monthly frequency if I have the data.
    
    all_pnls = df["net_pnl_pct"].values
    
    iteration_means = []
    for _ in range(n_iterations):
        sample = rng.choice(all_pnls, size=observed_count, replace=False)
        iteration_means.append(np.mean(sample))
        
    iteration_means = np.array(iteration_means)
    p95 = np.percentile(iteration_means, 95)
    mean_random = np.mean(iteration_means)
    
    percentile = (iteration_means < observed_mean_pnl).mean() * 100
    
    verdict = "BEATS_SAME_COUNT_RANDOM" if observed_mean_pnl > p95 else "FAILS_SAME_COUNT_RANDOM"
    if observed_count < 30:
        verdict = "SAME_COUNT_SAMPLE_TOO_SMALL"
        
    return {
        "observed_mean_pnl": observed_mean_pnl,
        "observed_count": observed_count,
        "random_mean": mean_random,
        "p95": p95,
        "percentile": percentile,
        "verdict": verdict
    }

def analyze_frequency_preserving_random(
    full_pool: pd.DataFrame,
    filtered_trades: pd.DataFrame,
    n_iterations: int = 1000,
    seed: int = 42
) -> dict[str, Any]:
    """Pick random trades while preserving the monthly count of the filtered set."""
    if full_pool.empty or filtered_trades.empty:
        return {}
        
    full_pool = full_pool.copy()
    filtered_trades = filtered_trades.copy()
    full_pool["month_key"] = full_pool["timestamp"].dt.to_period("M")
    filtered_trades["month_key"] = filtered_trades["timestamp"].dt.to_period("M")
    
    freq_map = filtered_trades.groupby("month_key").size().to_dict()
    
    rng = np.random.default_rng(seed)
    iteration_means = []
    
    for _ in range(n_iterations):
        sample_pnls = []
        for month, count in freq_map.items():
            month_pool = full_pool[full_pool["month_key"] == month]["net_pnl_pct"].values
            if len(month_pool) >= count:
                sample_pnls.extend(rng.choice(month_pool, size=count, replace=False))
            else:
                sample_pnls.extend(month_pool)
        
        if sample_pnls:
            iteration_means.append(np.mean(sample_pnls))
            
    iteration_means = np.array(iteration_means)
    observed_mean = float(filtered_trades["net_pnl_pct"].mean())
    p95 = float(np.percentile(iteration_means, 95))
    random_mean = float(np.mean(iteration_means))
    
    p_value = 1.0 - (iteration_means < observed_mean).mean()
    verdict = (
        "BEATS_MONTHLY_COUNT_RANDOM" if observed_mean > p95 
        else "NOT_DISTINGUISHABLE_FROM_MONTHLY_RANDOM"
    )
    
    return {
        "baseline_type": "monthly_count_preserving_random",
        "frequency_granularity": "month",
        "preserves_exact_timestamps": False,
        "preserves_monthly_counts": True,
        "preserves_weekly_counts": False,
        "observed_mean": observed_mean,
        "random_mean": random_mean,
        "p95": p95,
        "p_value_estimate": float(p_value),
        "verdict": verdict,
        "methodology_note": (
            "This baseline only preserves density at monthly scale. "
            "It does not account for intraday or weekly seasonality."
        )
    }
