"""Analyze feature predictive power decay for V1.43."""
from __future__ import annotations

import pandas as pd
from typing import Any

def analyze_predictive_power_decay(df: pd.DataFrame, usable_features: list[str]) -> dict[str, Any]:
    """Analyze if feature correlations with outcomes decay in 2026."""
    # We use forward_return_12bar as proxy for payoff/return as in V1.42.3
    target = "forward_return_12bar"
    if target not in df.columns:
        # Fallback to any forward return if 12bar missing
        target = [c for c in df.columns if "forward_return" in c][0] if any("forward_return" in c for c in df.columns) else None
        
    if not target:
        return {"predictive_power_status": "FEATURE_PREDICTIVE_POWER_INCONCLUSIVE", "decay_results": []}

    pre_2026 = df[df["timestamp"].dt.year < 2026]
    post_2026 = df[df["timestamp"].dt.year == 2026]
    
    if len(post_2026) == 0:
        return {"predictive_power_status": "FEATURE_PREDICTIVE_POWER_INCONCLUSIVE", "decay_results": []}

    decays = []
    for feat in usable_features:
        if feat not in df.columns or not pd.api.types.is_numeric_dtype(df[feat]):
            continue
            
        corr_pre = pre_2026[feat].corr(pre_2026[target])
        corr_post = post_2026[feat].corr(post_2026[target])
        
        decays.append({
            "feature": feat,
            "corr_pre_2026": float(corr_pre) if not pd.isna(corr_pre) else 0.0,
            "corr_2026": float(corr_post) if not pd.isna(corr_post) else 0.0,
            "abs_delta": abs(float(corr_post) - float(corr_pre)) if not (pd.isna(corr_pre) or pd.isna(corr_post)) else 0.0,
            "sign_flip": (float(corr_pre) * float(corr_post) < 0) if not (pd.isna(corr_pre) or pd.isna(corr_post)) else False
        })
        
    decay_df = pd.DataFrame(decays)
    if decay_df.empty:
         return {"predictive_power_status": "FEATURE_PREDICTIVE_POWER_INCONCLUSIVE", "decay_results": []}

    top_decayed = decay_df.sort_values("abs_delta", ascending=False).head(20).to_dict(orient="records")
    sign_flips = decay_df[decay_df["sign_flip"] == True]
    
    return {
        "predictive_power_status": "FEATURE_PREDICTIVE_POWER_DECAY_2026" if len(sign_flips) > 5 else "FEATURE_PREDICTIVE_POWER_STABLE",
        "total_audited": len(decays),
        "sign_flip_count": len(sign_flips),
        "top_decayed_features": top_decayed
    }
