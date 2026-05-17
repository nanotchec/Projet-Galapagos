"""Overfit guard for V1.44 research."""
from __future__ import annotations

from typing import Any

def check_overfit_risk(
    eval_results: dict[str, Any],
    max_sets_limit: int = 10
) -> dict[str, Any]:
    """Assess the risk of overfitting through multiple testing."""
    
    set_count = len(eval_results)
    
    risk_level = "LOW"
    if set_count > max_sets_limit:
        risk_level = "HIGH"
    elif set_count > max_sets_limit // 2:
        risk_level = "MODERATE"
        
    return {
        "status": "OVERFIT_GUARD_COMPLETE",
        "tested_set_count": set_count,
        "max_sets_limit": max_sets_limit,
        "overfit_risk_level": risk_level,
        "multiple_testing_penalty_applied": risk_level != "LOW"
    }
