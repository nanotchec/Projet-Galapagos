"""Analyze regime coverage for V1.43 diagnostic."""
from __future__ import annotations

import pandas as pd
from typing import Any

def analyze_regime_coverage(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze if 2026 regimes differ significantly from historical distributions."""
    regime_cols = [c for c in df.columns if "regime" in c.lower()]
    if not regime_cols:
        return {"regime_coverage_status": "REGIME_COVERAGE_INCONCLUSIVE"}
        
    pre_2026 = df[df["timestamp"].dt.year < 2026]
    post_2026 = df[df["timestamp"].dt.year == 2026]
    
    if len(post_2026) == 0:
        return {"regime_coverage_status": "REGIME_COVERAGE_INCONCLUSIVE"}
        
    coverage_shifts = {}
    for col in regime_cols:
        dist_pre = pre_2026[col].value_counts(normalize=True).to_dict()
        dist_post = post_2026[col].value_counts(normalize=True).to_dict()
        
        coverage_shifts[col] = {
            "pre_2026_dist": dist_pre,
            "post_2026_dist": dist_post,
            "new_regimes": [r for r in dist_post if r not in dist_pre],
            "missing_regimes": [r for r in dist_pre if r not in dist_post]
        }
        
    status = "REGIME_COVERAGE_BALANCED"
    for col, shift in coverage_shifts.items():
        if shift["new_regimes"] or shift["missing_regimes"]:
            status = "REGIME_COVERAGE_SHIFT_2026"
            break
            
    return {
        "regime_coverage_status": status,
        "regime_shifts": coverage_shifts
    }
