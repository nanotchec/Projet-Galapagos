"""Audit regime definitions for V1.43."""
from __future__ import annotations

import pandas as pd
from typing import Any

def audit_regime_definitions(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze the granularity and coverage of current regime proxies."""
    regime_cols = [c for c in df.columns if "regime" in c.lower()]
    
    if not regime_cols:
        return {
            "regime_definition_status": "REGIME_DEFINITION_MISSING",
            "regime_cols": [],
            "regime_distributions": {}
        }
        
    distributions = {}
    for col in regime_cols:
        counts = df[col].value_counts(normalize=True).to_dict()
        unique_vals = len(counts)
        distributions[col] = {
            "unique_values": unique_vals,
            "counts": counts,
            "dominant_regime_ratio": max(counts.values()) if counts else 0.0
        }
        
    # Heuristic: if all regime cols have very few unique values, they might be too coarse
    max_unique = max(d["unique_values"] for d in distributions.values())
    
    status = "REGIME_DEFINITION_AVAILABLE"
    if max_unique < 3:
        status = "REGIME_DEFINITION_TOO_COARSE"
        
    return {
        "regime_definition_status": status,
        "regime_cols": regime_cols,
        "regime_distributions": distributions
    }
