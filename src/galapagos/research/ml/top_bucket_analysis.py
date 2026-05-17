"""Top-bucket forward return analysis for ML confidence deciles."""
from __future__ import annotations

from typing import Any

import numpy as np


def analyze_top_bucket(
    y_proba: np.ndarray,
    forward_returns: np.ndarray,
    cost_threshold: float = 0.003,
) -> dict[str, Any]:
    """Analyze forward returns for top confident predictions."""
    if len(y_proba) == 0 or len(forward_returns) == 0 or len(y_proba) != len(forward_returns):
        return {"status": "invalid_input"}
        
    # We sort by probability descending
    idx = np.argsort(y_proba)[::-1]
    sorted_returns = forward_returns[idx]
    
    n = len(y_proba)
    
    def _metrics_for_percent(pct: float) -> dict[str, Any]:
        count = max(1, int(n * pct))
        bucket = sorted_returns[:count]
        return {
            "count": count,
            "mean_return": float(np.mean(bucket)),
            "median_return": float(np.median(bucket)),
            "hit_rate": float(np.mean(bucket > 0)),
            "cost_adjusted_return": float(np.mean(bucket - cost_threshold)),
            "mfe": float(np.max(bucket)) if count > 0 else 0.0, # approximation
            "mae": float(np.min(bucket)) if count > 0 else 0.0,
        }
        
    top_5 = _metrics_for_percent(0.05)
    top_10 = _metrics_for_percent(0.10)
    top_20 = _metrics_for_percent(0.20)
    
    # Bottom 20% for symmetry check
    bottom_count = max(1, int(n * 0.20))
    bottom_bucket = sorted_returns[-bottom_count:]
    bottom_20 = {
        "count": bottom_count,
        "mean_return": float(np.mean(bottom_bucket)),
        "hit_rate": float(np.mean(bottom_bucket > 0)),
    }
    
    # Verdict logic based on top 10%
    verdict = "TOP_BUCKET_NO_EDGE"
    if top_10["count"] < 30:
        verdict = "TOP_BUCKET_NEEDS_MORE_DATA"
    elif top_10["mean_return"] > cost_threshold:
        if top_10["cost_adjusted_return"] <= 0:
            verdict = "TOP_BUCKET_EDGE_DESTROYED_BY_COSTS"
        else:
            verdict = "TOP_BUCKET_WEAK_EDGE_BEFORE_COSTS"
            
        if top_10["cost_adjusted_return"] > 0:
            verdict = "TOP_BUCKET_PROMISING_BUT_SMALL_SAMPLE" if top_10["count"] < 100 else "TOP_BUCKET_BEATS_COSTS"
            
    return {
        "status": "computed",
        "sample_size": n,
        "top_5": top_5,
        "top_10": top_10,
        "top_20": top_20,
        "bottom_20": bottom_20,
        "verdict": verdict,
    }
