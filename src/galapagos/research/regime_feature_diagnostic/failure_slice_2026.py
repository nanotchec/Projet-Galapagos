"""Analyze 2026 failure slices for V1.43 diagnostic."""
from __future__ import annotations

import pandas as pd
from typing import Any

def analyze_2026_failure_slices(df: pd.DataFrame, usable_features: list[str]) -> dict[str, Any]:
    """Identify if 2026 failures are concentrated in specific feature/regime slices."""
    target = "forward_return_12bar"
    if target not in df.columns:
         target = [c for c in df.columns if "forward_return" in c][0] if any("forward_return" in c for c in df.columns) else None

    if not target:
        return {"failure_slice_status": "FAILURE_SLICE_2026_INCONCLUSIVE"}

    df_2026 = df[df["timestamp"].dt.year == 2026].copy()
    if df_2026.empty:
        return {"failure_slice_status": "FAILURE_SLICE_2026_INCONCLUSIVE"}
        
    # Define "failure" as the bottom 20% of returns in 2026
    threshold = df_2026[target].quantile(0.2)
    df_2026["is_failure"] = df_2026[target] <= threshold
    
    failures = df_2026[df_2026["is_failure"]]
    successes = df_2026[~df_2026["is_failure"]]
    
    # Check regime concentration
    regime_col = "macro_regime" if "macro_regime" in df.columns else None
    failure_patterns = {}
    if regime_col:
        regime_dist_fail = failures[regime_col].value_counts(normalize=True).to_dict()
        regime_dist_all = df_2026[regime_col].value_counts(normalize=True).to_dict()
        failure_patterns["regime_concentration"] = {
            "failure_dist": regime_dist_fail,
            "overall_dist": regime_dist_all
        }
        
    # Identify features that differentiate failures
    diff_features = []
    for feat in usable_features[:50]:
        if feat not in df_2026.columns or not pd.api.types.is_numeric_dtype(df_2026[feat]):
            continue
            
        m_fail = failures[feat].mean()
        m_succ = successes[feat].mean()
        std_all = df_2026[feat].std()
        
        if std_all > 0:
            diff = (m_fail - m_succ) / std_all
            if abs(diff) > 0.5:
                diff_features.append({
                    "feature": feat,
                    "diff_score": float(diff)
                })
                
    return {
        "failure_slice_status": "FAILURE_SLICE_2026_FEATURE_REGIME_PATTERN_FOUND" if diff_features else "FAILURE_SLICE_2026_DIFFUSE",
        "failure_threshold": float(threshold),
        "differentiating_features": sorted(diff_features, key=lambda x: abs(x["diff_score"]), reverse=True)[:10],
        "regime_patterns": failure_patterns
    }
