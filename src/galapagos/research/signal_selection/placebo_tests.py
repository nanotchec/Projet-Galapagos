from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def run_placebo_tests(
    df: pd.DataFrame, 
    filtered_indices: pd.Index,
    n_iterations: int = 1000,
    seed: int = 42
) -> dict[str, Any]:
    """Run various placebo tests to detect spurious correlations."""
    if df.empty or len(filtered_indices) == 0:
        return {}
        
    rng = np.random.default_rng(seed)
    observed_mean = df.loc[filtered_indices, "net_pnl_pct"].mean()
    
    results = {}
    
    # 1. Random Same-Count Placebo (formerly shuffle_timestamps)
    shuffle_means = []
    all_pnls = df["net_pnl_pct"].values
    for _ in range(n_iterations):
        shuffle_means.append(rng.choice(all_pnls, size=len(filtered_indices), replace=False).mean())
    
    shuffle_means = np.array(shuffle_means)
    results["random_same_count_placebo"] = {
        "placebo_type": "random_unconditional_pick",
        "re_applies_filter": False,
        "preserves_filter_logic": False,
        "observed": float(observed_mean),
        "p95": float(np.percentile(shuffle_means, 95)),
        "verdict": "PLACEBO_PARTIAL_PASS" if observed_mean > np.percentile(shuffle_means, 95) else "PLACEBO_FAILS",
        "limitation": (
            "Does not re-apply filter logic on shuffled data; "
            "only tests if count-based performance is outlier."
        )
    }
    
    # 2. Random Weekly Pick Placebo (formerly random_weekly_picks)
    df = df.copy()
    df["week"] = df["timestamp"].dt.to_period("W")
    weekly_means = []
    for _ in range(100): 
        # sample 1 per week
        sample = df.groupby("week", group_keys=False).apply(
            lambda x: x.sample(1, random_state=rng.integers(1e9))
        )
        weekly_means.append(sample["net_pnl_pct"].mean())
    
    results["random_weekly_pick_placebo"] = {
        "placebo_type": "random_stratified_weekly_pick",
        "re_applies_filter": False,
        "preserves_filter_logic": False,
        "observed": float(observed_mean),
        "mean": float(np.mean(weekly_means)),
        "p95": float(np.percentile(weekly_means, 95)),
        "verdict": (
            "PLACEBO_INCOMPLETE" if len(weekly_means) < 30 
            else "PLACEBO_PARTIAL_PASS" if observed_mean > np.percentile(weekly_means, 95) 
            else "PLACEBO_FAILS"
        ),
        "limitation": "Does not account for filter selection criteria beyond temporal density."
    }
    
    results["placebo_status"] = "PLACEBO_PARTIAL"
    
    return results
