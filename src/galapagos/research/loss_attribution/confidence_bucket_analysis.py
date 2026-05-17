from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_confidence_buckets(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze if model confidence correlates with net returns."""
    if df.empty or "confidence" not in df.columns:
        return {}
        
    def get_bucket(conf):
        if conf < 0.55: return "0.50-0.55"
        if conf < 0.60: return "0.55-0.60"
        if conf < 0.65: return "0.60-0.65"
        if conf < 0.70: return "0.65-0.70"
        return "0.70+"
        
    df["conf_bucket"] = df["confidence"].apply(get_bucket)
    
    stats = df.groupby("conf_bucket")["net_pnl_pct"].agg(["count", "mean", "sum"]).to_dict(orient="index")
    
    # Check monotonicity
    means = [stats[b]["mean"] for b in sorted(stats.keys()) if b in stats]
    is_monotonic = all(x <= y for x, y in zip(means, means[1:])) if len(means) > 1 else False
    
    verdict = "PROBABILITY_EDGE_TOO_WEAK"
    if is_monotonic and means[-1] > 0:
        verdict = "TOP_BUCKET_PROMISING_BUT_UNVALIDATED"
    elif means and max(means) < 0:
        verdict = "HIGH_CONFIDENCE_STILL_NEGATIVE"
        
    return {
        "buckets": stats,
        "is_monotonic": is_monotonic,
        "verdict": verdict
    }
