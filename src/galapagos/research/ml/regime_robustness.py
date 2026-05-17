"""Regime and year robustness analysis."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def analyze_regime_robustness(
    dataset_slice: pd.DataFrame,
    y_pred: np.ndarray,
    y_true: np.ndarray,
) -> dict[str, Any]:
    """Group metrics by year and predefined regimes."""
    if len(dataset_slice) != len(y_pred):
        return {"status": "dimension_mismatch"}
        
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(dataset_slice["timestamp"], utc=True),
        "y_true": y_true,
        "y_pred": y_pred,
    })
    
    # Extract year
    df["year"] = df["timestamp"].dt.year
    
    # Simple regimes based on provided columns if they exist
    if "trend_slope_42" in dataset_slice.columns:
        df["trend"] = np.where(
            dataset_slice["trend_slope_42"] > 0, "uptrend", "downtrend",
        )
    else:
        df["trend"] = "unknown"
        
    if "realized_vol_42" in dataset_slice.columns:
        vol_median = dataset_slice["realized_vol_42"].median()
        df["volatility"] = np.where(
            dataset_slice["realized_vol_42"] > vol_median, "high_vol", "low_vol",
        )
    else:
        df["volatility"] = "unknown"
        
    def _metrics_for_group(group: pd.DataFrame) -> dict[str, Any]:
        acc = float(np.mean(group["y_true"] == group["y_pred"]))
        return {
            "count": len(group),
            "accuracy": acc,
            "base_rate": float(np.mean(group["y_true"])),
        }
        
    years = {}
    for year, g in df.groupby("year"):
        years[str(year)] = _metrics_for_group(g)
        
    trends = {}
    for trend, g in df.groupby("trend"):
        trends[str(trend)] = _metrics_for_group(g)
        
    vols = {}
    for vol, g in df.groupby("volatility"):
        vols[str(vol)] = _metrics_for_group(g)
        
    # Verdict simple
    verdict = "ML_STABLE_ACROSS_REGIMES"
    # If accuracy drops significantly below base_rate in any large group -> unstable
    for g_dict in [years, trends, vols]:
        for _k, m in g_dict.items():
            if m["count"] > 100 and m["accuracy"] < m["base_rate"] - 0.05:
                verdict = "ML_UNSTABLE_BY_REGIME"
                break
                
    return {
        "status": "computed",
        "by_year": years,
        "by_trend": trends,
        "by_volatility": vols,
        "verdict": verdict,
    }
