"""Analyze regime breakdown of targets."""
from __future__ import annotations

import pandas as pd
from typing import Any

def analyze_regime_breakdown(df: pd.DataFrame, target_meta: dict[str, Any]) -> dict[str, Any]:
    """Analyze target performance by market regime."""
    if "macro_regime" not in df.columns:
        return {"status": "PAYOFF_TARGET_REGIME_DATA_LIMITED"}
        
    regimes = df["macro_regime"].unique()
    results = {}
    
    for regime in regimes:
        regime_df = df[df["macro_regime"] == regime]
        regime_results = {}
        for t in target_meta.get("targets", []):
            col = t["label_column_used"]
            regime_results[t["target_name"]] = {
                "mean": float(regime_df[col].mean()),
                "count": len(regime_df)
            }
        results[str(regime)] = regime_results
        
    return {
        "status": "PAYOFF_TARGET_REGIME_BREAKDOWN_COMPLETE",
        "regime_stats": results
    }
