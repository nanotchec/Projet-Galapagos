from __future__ import annotations

import pandas as pd


def analyze_agreement_buckets(
    df: pd.DataFrame,
    agreement_col: str,
    return_col: str,
    cost_threshold: float = 0.003,
) -> pd.DataFrame:
    """Group metrics by agreement level."""
    bins = [0, 0.5, 0.6, 0.7, 0.8, 1.0]
    labels = ["<0.5", "0.5-0.6", "0.6-0.7", "0.7-0.8", ">0.8"]
    
    df_temp = df.copy()
    df_temp["agreement_bucket"] = pd.cut(df[agreement_col], bins=bins, labels=labels)
    
    stats = []
    for label in labels:
        subset = df_temp[df_temp["agreement_bucket"] == label]
        if len(subset) == 0:
            continue
            
        mean_ret = subset[return_col].mean()
        hit_rate = (subset[return_col] > 0).mean()
        cost_adj = (subset[return_col] - cost_threshold).mean()
        
        stats.append({
            "agreement_bucket": label,
            "count": len(subset),
            "mean_return": float(mean_ret),
            "hit_rate": float(hit_rate),
            "cost_adjusted_return": float(cost_adj),
        })
        
    # Compute agreement verdict
    verdict = "AGREEMENT_INSUFFICIENT_DATA"
    high_agreement = [s for s in stats if s["agreement_bucket"] == ">0.8"]
    if high_agreement:
        net_ret = high_agreement[0]["cost_adjusted_return"]
        verdict = "AGREEMENT_IMPROVES_SIGNAL" if net_ret > 0 else "AGREEMENT_NO_ECONOMIC_EDGE"
    elif len(stats) > 0:
        verdict = "AGREEMENT_REGIME_DEPENDENT"

    return pd.DataFrame(stats), verdict
