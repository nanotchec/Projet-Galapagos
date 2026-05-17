"""Extract and analyze return horizons for payoff research."""
from __future__ import annotations

import pandas as pd
import numpy as np

def build_horizon_candidates(frame: pd.DataFrame) -> dict[str, Any]:
    """Analyze available return horizons in the dataset."""
    horizons = [
        "forward_return_3bar",
        "forward_return_6bar",
        "forward_return_12bar",
        "cost_adjusted_forward_return"
    ]
    
    candidates = {}
    missing_horizons = []
    
    # 2026 filter
    is_2026 = frame["timestamp_year"] == 2026
    
    for h in horizons:
        if h not in frame.columns:
            missing_horizons.append(h)
            continue
            
        series = pd.to_numeric(frame[h], errors="coerce").dropna()
        if series.empty:
            missing_horizons.append(h)
            continue
            
        series_2026 = pd.to_numeric(frame.loc[is_2026, h], errors="coerce").dropna()
        
        # Simple signal to noise proxy: mean / std
        snr = series.mean() / series.std() if series.std() > 0 else 0
        
        candidates[h] = {
            "availability": "AVAILABLE",
            "row_count": len(series),
            "row_count_2026": len(series_2026),
            "mean_return": float(series.mean()),
            "std_return": float(series.std()),
            "downside_rate": float((series < 0).mean()),
            "near_zero_rate": float((series.abs() < 0.0001).mean()),
            "signal_to_noise_proxy": float(snr),
            "label_noise_proxy": float(1.0 - abs(snr)) # Higher if SNR is low
        }
        
    status = "PAYOFF_TARGET_HORIZONS_DEFINED" if candidates else "PAYOFF_TARGET_HORIZONS_FAILED"
    if missing_horizons and candidates:
        status = "PAYOFF_TARGET_HORIZONS_PARTIAL"
        
    return {
        "status": status,
        "candidates": candidates,
        "missing_horizons": missing_horizons
    }
