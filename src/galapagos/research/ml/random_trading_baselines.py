"""Random trading-like baselines for ML evaluation."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def majority_class_baseline(y_true: np.ndarray) -> dict[str, Any]:
    """Simple baseline predicting the majority class always."""
    if len(y_true) == 0:
        return {"status": "no_data"}
    mean = y_true.mean()
    pred = 1.0 if mean >= 0.5 else 0.0
    acc = mean if pred == 1.0 else (1 - mean)
    return {"accuracy": acc, "majority_class": pred, "status": "computed"}


def random_entries_same_count(
    dataset: pd.DataFrame,
    entry_count: int,
    forward_return_col: str = "forward_return_12bar",
    n_trials: int = 1000,
    seed: int = 42,
) -> dict[str, Any]:
    """Randomly pick `entry_count` points and compute returns. Repeat `n_trials` times."""
    if len(dataset) < entry_count or entry_count == 0:
        return {"status": "insufficient_data"}
    if forward_return_col not in dataset.columns:
        return {"status": "missing_column", "column": forward_return_col}
        
    rng = np.random.RandomState(seed)
    returns = dataset[forward_return_col].fillna(0).values
    
    trial_means = []
    trial_hits = []
    
    for _ in range(n_trials):
        idx = rng.choice(len(returns), size=entry_count, replace=False)
        sample = returns[idx]
        trial_means.append(sample.mean())
        trial_hits.append((sample > 0).mean())
        
    return {
        "status": "computed",
        "entry_count": entry_count,
        "n_trials": n_trials,
        "mean_forward_return": float(np.mean(trial_means)),
        "mean_hit_rate": float(np.mean(trial_hits)),
        "std_forward_return": float(np.std(trial_means)),
        "distribution_percentiles": {
            "5": float(np.percentile(trial_means, 5)),
            "50": float(np.percentile(trial_means, 50)),
            "95": float(np.percentile(trial_means, 95)),
        },
        "raw_trials": trial_means,  # Keep for percentile ranking later
    }


def compute_random_percentile(real_value: float, trials: list[float]) -> float:
    """Compute percentile of real_value within the distribution of trials."""
    if not trials:
        return 0.0
    return float(np.mean([t <= real_value for t in trials]) * 100)


def compute_p_value(real_value: float, trials: list[float]) -> float:
    """Compute one-sided p-value (probability of getting a value >= real_value under null)."""
    if not trials:
        return 1.0
    return float(np.mean([t >= real_value for t in trials]))
