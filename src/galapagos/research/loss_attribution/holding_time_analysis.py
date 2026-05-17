from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_holding_time(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze PnL by trade duration."""
    if df.empty:
        return {}
        
    # Duration is in seconds (assumed from simulator)
    # Buckets
    def get_bucket(sec):
        if sec < 3600: return "< 1h"
        if sec < 3600 * 4: return "1-4h"
        if sec < 3600 * 12: return "4-12h"
        if sec < 3600 * 24: return "12-24h"
        if sec < 3600 * 24 * 3: return "1-3j"
        return "> 3j"
        
    df["duration_bucket"] = df["duration"].apply(get_bucket)
    
    stats = df.groupby("duration_bucket")["net_pnl_pct"].agg(["count", "mean", "sum"])
    buckets_dict = stats.to_dict(orient="index")
    
    verdict = "HOLDING_TIME_NOT_PRIMARY_DRIVER"
    # If short trades are significantly worse
    if "< 1h" in buckets_dict and buckets_dict["< 1h"]["mean"] < df["net_pnl_pct"].mean() * 2:
        verdict = "SHORT_HOLDING_UNPROFITABLE"
        
    return {
        "buckets": buckets_dict,
        "mean_duration_seconds": df["duration"].mean(),
        "median_duration_seconds": df["duration"].median(),
        "verdict": verdict
    }
