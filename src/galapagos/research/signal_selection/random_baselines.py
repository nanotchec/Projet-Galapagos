"""Random same-count baselines for selected signal subsets."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def random_same_count_baseline(
    population: pd.DataFrame,
    selected_count: int,
    *,
    iterations: int = 500,
    seed: int = 2401,
) -> dict[str, Any]:
    if selected_count <= 0 or population.empty:
        return {
            "selected_count": selected_count,
            "iterations": iterations,
            "random_mean": 0.0,
            "random_std": 0.0,
            "random_p05": 0.0,
            "random_p95": 0.0,
            "samples": [],
        }
    rng = np.random.default_rng(seed)
    net = pd.to_numeric(population["net_pnl_pct"], errors="coerce").fillna(0.0).to_numpy()
    replace = selected_count > len(net)
    samples = []
    for _ in range(iterations):
        idx = rng.choice(len(net), size=selected_count, replace=replace)
        samples.append(float(net[idx].mean()))
    arr = np.array(samples, dtype=float)
    return {
        "selected_count": selected_count,
        "iterations": iterations,
        "random_mean": float(arr.mean()),
        "random_std": float(arr.std(ddof=0)),
        "random_p05": float(np.quantile(arr, 0.05)),
        "random_p95": float(np.quantile(arr, 0.95)),
        "samples": samples[:100],
    }


def observed_percentile(observed: float, samples: list[float]) -> float:
    if not samples:
        return 0.0
    arr = np.array(samples, dtype=float)
    return float((arr <= observed).mean())
