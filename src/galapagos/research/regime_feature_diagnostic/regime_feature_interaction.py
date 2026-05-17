"""Analyze regime-feature interactions for V1.43 diagnostic."""
from __future__ import annotations

import pandas as pd
from typing import Any

def analyze_regime_feature_interactions(df: pd.DataFrame, usable_features: list[str]) -> dict[str, Any]:
    """Identify which features become unstable in specific regimes."""
    regime_col = "macro_regime" if "macro_regime" in df.columns else None
    if not regime_col:
        regime_cols = [c for c in df.columns if "regime" in c.lower()]
        regime_col = regime_cols[0] if regime_cols else None
        
    if not regime_col:
        return {"regime_feature_interaction_status": "REGIME_FEATURE_INTERACTION_INCONCLUSIVE"}
        
    # We focus on the dominant regime in 2026 to see if features drifted there
    post_2026 = df[df["timestamp"].dt.year == 2026]
    if post_2026.empty:
        return {"regime_feature_interaction_status": "REGIME_FEATURE_INTERACTION_INCONCLUSIVE"}
        
    dominant_regime_2026 = post_2026[regime_col].mode().iloc[0] if not post_2026[regime_col].mode().empty else None
    
    if dominant_regime_2026 is None:
        return {"regime_feature_interaction_status": "REGIME_FEATURE_INTERACTION_INCONCLUSIVE"}
        
    # Compare feature distribution in THIS regime: historical vs 2026
    in_regime = df[df[regime_col] == dominant_regime_2026]
    pre_regime = in_regime[in_regime["timestamp"].dt.year < 2026]
    post_regime = in_regime[in_regime["timestamp"].dt.year == 2026]
    
    if pre_regime.empty or post_regime.empty:
        return {"regime_feature_interaction_status": "REGIME_FEATURE_INTERACTION_LIMITED"}
        
    unstable_in_regime = []
    for feat in usable_features[:50]: # Limit for performance
        if feat not in df.columns or not pd.api.types.is_numeric_dtype(df[feat]):
            continue
            
        m_pre = pre_regime[feat].mean()
        s_pre = pre_regime[feat].std()
        m_post = post_regime[feat].mean()
        
        drift = abs(m_post - m_pre) / s_pre if s_pre > 0 else 0.0
        if drift > 1.0:
            unstable_in_regime.append({
                "feature": feat,
                "regime": str(dominant_regime_2026),
                "drift_in_regime": float(drift)
            })
            
    return {
        "regime_feature_interaction_status": "REGIME_FEATURE_INTERACTION_DRIFT_DETECTED" if unstable_in_regime else "REGIME_FEATURE_INTERACTION_LIMITED",
        "dominant_regime_2026": str(dominant_regime_2026),
        "unstable_features_in_dominant_regime": unstable_in_regime
    }
