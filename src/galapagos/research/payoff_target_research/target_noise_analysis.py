"""Analyze noise and stability of defined targets."""
from __future__ import annotations

import pandas as pd
import numpy as np

def analyze_target_noise(df: pd.DataFrame, target_meta: dict[str, Any]) -> dict[str, Any]:
    """Analyze noise characteristics of targets."""
    results = []
    
    is_2026 = df["timestamp_year"] == 2026
    
    for t in target_meta.get("targets", []):
        col = t["label_column_used"]
        series = df[col].dropna()
        if series.empty:
            continue
            
        series_2026 = df.loc[is_2026, col].dropna()
        series_pre = df.loc[~is_2026, col].dropna()
        
        noise_proxy_total = series.std() / (series.abs().mean() + 1e-6)
        noise_proxy_2026 = series_2026.std() / (series_2026.abs().mean() + 1e-6)
        
        results.append({
            "target_name": t["target_name"],
            "near_zero_rate": float((series.abs() < 1e-5).mean()),
            "return_std": float(series.std()),
            "signal_to_noise_proxy": float(1.0 / (noise_proxy_total + 1e-6)),
            "noise_2026_vs_pre": float(noise_proxy_2026 / (noise_proxy_total + 1e-6)),
            "label_balance": float((series > 0).mean()) if t.get("threshold") is None else float(series.mean()),
            "target_stability_score": float(1.0 - abs(noise_proxy_2026 - noise_proxy_total) / (noise_proxy_total + 1e-6))
        })
        
    status = "PAYOFF_TARGET_NOISE_ACCEPTABLE"
    if any(r["signal_to_noise_proxy"] < 0.1 for r in results):
        status = "PAYOFF_TARGET_NOISE_HIGH"
        
    return {
        "status": status,
        "results": results
    }
