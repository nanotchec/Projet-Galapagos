"""Probability calibration analysis for ML research."""
from __future__ import annotations

from typing import Any

import numpy as np


def calibration_analysis(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    *,
    n_bins: int = 5,
) -> dict[str, Any]:
    """Compute reliability curve bins and Brier score."""
    n = len(y_true)
    if n == 0 or y_proba is None:
        return {"status": "no_data", "bins": [], "brier_score": None}

    # Brier score
    brier = float(np.mean((y_proba - y_true) ** 2))

    # Reliability curve
    bins: list[dict] = []
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (y_proba >= lo) & (y_proba < hi if i < n_bins - 1 else y_proba <= hi)
        count = int(mask.sum())
        if count == 0:
            bins.append({
                "bin_low": float(lo), "bin_high": float(hi),
                "count": 0, "mean_predicted": None, "observed_rate": None,
            })
            continue
        mean_pred = float(y_proba[mask].mean())
        observed = float(y_true[mask].mean())
        bins.append({
            "bin_low": float(lo),
            "bin_high": float(hi),
            "count": count,
            "mean_predicted": mean_pred,
            "observed_rate": observed,
        })

    # Calibration quality
    calibration_gap = _max_calibration_gap(bins)
    well_calibrated = calibration_gap < 0.10

    return {
        "status": "computed",
        "brier_score": brier,
        "n_bins": n_bins,
        "bins": bins,
        "max_calibration_gap": calibration_gap,
        "well_calibrated": well_calibrated,
        "warning": None if well_calibrated else "probabilities_not_calibrated",
    }


def _max_calibration_gap(bins: list[dict]) -> float:
    """Max absolute difference between predicted and observed across bins."""
    gaps = []
    for b in bins:
        if b["mean_predicted"] is not None and b["observed_rate"] is not None:
            gaps.append(abs(b["mean_predicted"] - b["observed_rate"]))
    return max(gaps) if gaps else 0.0
