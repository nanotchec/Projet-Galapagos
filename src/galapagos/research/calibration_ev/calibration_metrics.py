from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import brier_score_loss, log_loss


def calculate_calibration_metrics(
    y_true: np.ndarray, 
    y_prob: np.ndarray, 
    n_bins: int = 10
) -> dict[str, Any]:
    """
    Calculate global calibration metrics.
    """
    if len(y_true) == 0:
        return {"status": "CALIBRATION_DATA_MISSING"}
        
    try:
        brier = brier_score_loss(y_true, y_prob)
        # log_loss requires at least 2 classes in y_true usually, or labels provided
        ll = log_loss(y_true, y_prob, labels=[0, 1])
        
        # ECE (Expected Calibration Error)
        bins = np.linspace(0., 1. + 1e-8, n_bins + 1)
        binids = np.digitize(y_prob, bins) - 1
        
        bin_sums = np.bincount(binids, weights=y_prob, minlength=len(bins))
        bin_true = np.bincount(binids, weights=y_true, minlength=len(bins))
        bin_total = np.bincount(binids, minlength=len(bins))
        
        nonzero = bin_total > 0
        prob_true = bin_true[nonzero] / bin_total[nonzero]
        prob_pred = bin_sums[nonzero] / bin_total[nonzero]
        
        ece = np.sum(np.abs(prob_true - prob_pred) * (bin_total[nonzero] / len(y_true)))
        mce = np.max(np.abs(prob_true - prob_pred)) if len(prob_true) > 0 else 0.0
        
        return {
            "brier_score": float(brier),
            "log_loss": float(ll),
            "ece": float(ece),
            "mce": float(mce),
            "sample_count": len(y_true),
            "status": "CALIBRATION_ACCEPTABLE_EXPLORATORY" if ece < 0.1 else "CALIBRATION_DEGRADED"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "CALIBRATION_NOT_INTERPRETABLE",
            "probability_interpretation_warning": True
        }
