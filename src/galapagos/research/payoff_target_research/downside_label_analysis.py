"""Analyze downside capture capability of targets."""
from __future__ import annotations

import pandas as pd
import numpy as np

def analyze_downside_labels(df: pd.DataFrame, target_meta: dict[str, Any]) -> dict[str, Any]:
    """Analyze if targets correctly isolate severe losses."""
    # Define severe loss in net return
    threshold = -0.01
    actual_net_ret = df["target_net_return"] # This was defined in target_definitions
    is_severe = actual_net_ret < threshold
    
    results = []
    for t in target_meta.get("targets", []):
        col = t["label_column_used"]
        label_val = df[col]
        
        # Simple correlation with severe loss indicator
        corr = label_val.corr(is_severe.astype(float))
        
        results.append({
            "target_name": t["target_name"],
            "severe_loss_threshold": threshold,
            "severe_loss_correlation": float(corr),
            "downside_focus": t["downside_focus_level"]
        })
        
    status = "DOWNSIDE_LABEL_CAPTURES_SEVERE_LOSSES" if any(r["severe_loss_correlation"] > 0.3 for r in results) else "DOWNSIDE_LABEL_MISSES_SEVERE_LOSSES"
    
    return {
        "status": status,
        "results": results,
        "severe_loss_count": int(is_severe.sum()),
        "severe_loss_rate": float(is_severe.mean())
    }
