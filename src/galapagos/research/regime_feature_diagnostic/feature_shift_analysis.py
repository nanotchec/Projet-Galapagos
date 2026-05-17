"""Analyze feature distribution shifts for V1.43."""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any

def analyze_feature_shifts(df: pd.DataFrame, usable_features: list[str]) -> dict[str, Any]:
    """Detect distribution shifts between pre-2026 and 2026."""
    pre_2026 = df[df["timestamp"].dt.year < 2026]
    post_2026 = df[df["timestamp"].dt.year == 2026]
    
    if len(post_2026) == 0:
        return {"feature_shift_status": "REGIME_FEATURE_SHIFT_NOT_DETECTED", "shifts": []}
        
    shifts = []
    for feat in usable_features:
        if feat not in df.columns:
            continue
            
        # Numerical features only for mean/std
        if not pd.api.types.is_numeric_dtype(df[feat]):
            continue
            
        m_pre = pre_2026[feat].mean()
        s_pre = pre_2026[feat].std()
        m_post = post_2026[feat].mean()
        s_post = post_2026[feat].std()
        
        # Simple drift score: z-score of the mean shift
        drift_score = 0.0
        if s_pre > 0:
            drift_score = abs(m_post - m_pre) / s_pre
            
        shifts.append({
            "feature": feat,
            "mean_pre_2026": float(m_pre) if not pd.isna(m_pre) else None,
            "mean_2026": float(m_post) if not pd.isna(m_post) else None,
            "std_pre_2026": float(s_pre) if not pd.isna(s_pre) else None,
            "std_2026": float(s_post) if not pd.isna(s_post) else None,
            "drift_score": float(drift_score)
        })
        
    shift_df = pd.DataFrame(shifts)
    if shift_df.empty:
         return {"feature_shift_status": "REGIME_FEATURE_SHIFT_INCONCLUSIVE", "shifts": []}

    top_shifted = shift_df.sort_values("drift_score", ascending=False).head(20).to_dict(orient="records")
    severe_shifts = shift_df[shift_df["drift_score"] > 1.0]
    
    return {
        "feature_shift_status": "REGIME_FEATURE_SHIFT_DETECTED_2026" if len(severe_shifts) > 0 else "REGIME_FEATURE_SHIFT_LIMITED",
        "severe_shift_count": len(severe_shifts),
        "total_audited": len(shifts),
        "top_shifted_features": top_shifted
    }
