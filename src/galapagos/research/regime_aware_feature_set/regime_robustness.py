"""Regime robustness evaluation for V1.44 research."""
from __future__ import annotations

from typing import Any
import pandas as pd

def evaluate_regime_robustness(
    df: pd.DataFrame,
    feature_sets: dict[str, list[str]],
    target_col: str,
    regime_col: str = "macro_regime"
) -> dict[str, Any]:
    """Evaluate feature set stability across different market regimes."""
    
    if regime_col not in df.columns:
        return {"status": "REGIME_ROBUSTNESS_SKIPPED", "reason": f"No {regime_col} column"}

    regimes = df[regime_col].unique()
    
    results = {}
    for name, features in feature_sets.items():
        regime_metrics = {}
        for regime in regimes:
            slice_df = df[df[regime_col] == regime]
            if len(slice_df) < 50:
                continue
            
            corrs = []
            for feat in features:
                if feat in slice_df.columns and slice_df[feat].dtype in ['float64', 'int64']:
                    c = slice_df[feat].corr(slice_df[target_col])
                    corrs.append(abs(c))
            regime_metrics[str(regime)] = sum(corrs)/len(corrs) if corrs else 0.0
            
        results[name] = {
            "regime_stability": regime_metrics,
            "regime_invariant": "TRUE" if len(regime_metrics) > 1 and max(regime_metrics.values()) - min(regime_metrics.values()) < 0.15 else "FALSE"
        }
        
    return {
        "status": "REGIME_ROBUSTNESS_COMPLETE",
        "results": results,
        "regimes_evaluated": [str(r) for r in regimes]
    }
