from __future__ import annotations

import numpy as np
from sklearn.metrics import brier_score_loss, log_loss


def calculate_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """
    Expected Calibration Error (ECE).
    """
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for i in range(n_bins):
        mask = (y_prob >= bins[i]) & (y_prob < bins[i+1])
        if i == n_bins - 1:
            mask = (y_prob >= bins[i]) & (y_prob <= bins[i+1])
        
        if np.any(mask):
            conf = np.mean(y_prob[mask])
            acc = np.mean(y_true[mask])
            ece += (len(y_true[mask]) / n) * np.abs(conf - acc)
    return ece


def calculate_mce(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """
    Maximum Calibration Error (MCE).
    """
    bins = np.linspace(0, 1, n_bins + 1)
    mce = 0.0
    for i in range(n_bins):
        mask = (y_prob >= bins[i]) & (y_prob < bins[i+1])
        if i == n_bins - 1:
            mask = (y_prob >= bins[i]) & (y_prob <= bins[i+1])
        
        if np.any(mask):
            conf = np.mean(y_prob[mask])
            acc = np.mean(y_true[mask])
            mce = max(mce, np.abs(conf - acc))
    return mce


def get_calibration_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    return {
        "brier_score": brier_score_loss(y_true, y_prob),
        "ece": calculate_ece(y_true, y_prob),
        "mce": calculate_mce(y_true, y_prob),
        "log_loss": log_loss(y_true, y_prob)
    }
