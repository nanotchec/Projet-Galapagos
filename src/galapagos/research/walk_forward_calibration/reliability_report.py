from __future__ import annotations

from typing import Any

import numpy as np


def generate_reliability_bins_report(
    y_true: np.ndarray, 
    y_prob: np.ndarray, 
    split_id: str, 
    method_name: str, 
    n_bins: int = 10
) -> list[dict[str, Any]]:
    """
    Generate reliability bins for a specific split and method.
    """
    bins = np.linspace(0, 1, n_bins + 1)
    results = []
    
    for i in range(n_bins):
        low = bins[i]
        high = bins[i+1]
        
        mask = (y_prob >= low) & (y_prob < high)
        if i == n_bins - 1:
            mask = (y_prob >= low) & (y_prob <= high)
            
        sample_count = int(np.sum(mask))
        
        if sample_count > 0:
            avg_prob = float(np.mean(y_prob[mask]))
            emp_win_rate = float(np.mean(y_true[mask]))
            gap = float(np.abs(avg_prob - emp_win_rate))
            status = "BIN_READY"
        else:
            avg_prob = 0.0
            emp_win_rate = 0.0
            gap = 0.0
            status = "BIN_SAMPLE_TOO_SMALL"
            
        results.append({
            "split_id": split_id,
            "method": method_name,
            "bin_low": float(low),
            "bin_high": float(high),
            "sample_count": sample_count,
            "avg_predicted_probability": avg_prob,
            "empirical_win_rate": emp_win_rate,
            "calibration_gap": gap,
            "status": status
        })
        
    return results
