"""Analyze if microstructure regimes explain the 2026 performance degradation V1.49."""
from __future__ import annotations

import pandas as pd
from typing import Any

def explain_2026_failures(
    frame: pd.DataFrame,
    outcome_col: str = "target_4h_bin"
) -> dict[str, Any]:
    """Compare 2026 vs Pre-2026 regime distributions and outcomes."""
    if "is_2026" not in frame.columns:
        frame["is_2026"] = frame["timestamp"].dt.year == 2026
        
    pre_2026 = frame[~frame["is_2026"]]
    post_2026 = frame[frame["is_2026"]]
    
    if len(post_2026) == 0:
        return {"status": "NO_2026_DATA", "explanation": "No data for 2026 found in frame"}
        
    # Distribution shift
    pre_dist = pre_2026["micro_regime"].value_counts(normalize=True).to_dict()
    post_dist = post_2026["micro_regime"].value_counts(normalize=True).to_dict()
    
    # Outcome shift per regime
    regime_shift = {}
    unique_regimes = set(pre_dist.keys()) | set(post_dist.keys())
    
    for r in unique_regimes:
        pre_group = pre_2026[pre_2026["micro_regime"] == r]
        post_group = post_2026[post_2026["micro_regime"] == r]
        
        if outcome_col in frame.columns:
            pre_perf = pre_group[outcome_col].mean() if len(pre_group) > 0 else None
            post_perf = post_group[outcome_col].mean() if len(post_group) > 0 else None
        else:
            pre_perf = post_perf = None
            
        regime_shift[str(r)] = {
            "pre_2026_weight": pre_dist.get(r, 0),
            "post_2026_weight": post_dist.get(r, 0),
            "pre_2026_perf": float(pre_perf) if pre_perf is not None else None,
            "post_2026_perf": float(post_perf) if post_perf is not None else None,
            "weight_delta": post_dist.get(r, 0) - pre_dist.get(r, 0)
        }
        
    # Identify regimes that explain 2026 failure (e.g. regimes that became more frequent and have bad perf)
    explaining_regimes = [
        r for r, s in regime_shift.items() 
        if s["weight_delta"] > 0.05 and (s["post_2026_perf"] is not None and s["post_2026_perf"] < 0)
    ]

    return {
        "regime_shift_2026": regime_shift,
        "explaining_regimes": explaining_regimes,
        "total_2026_rows": len(post_2026),
        "total_pre_2026_rows": len(pre_2026)
    }
