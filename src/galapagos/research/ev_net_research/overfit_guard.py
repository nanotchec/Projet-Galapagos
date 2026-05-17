from __future__ import annotations

from typing import Any


def analyze_overfit_risk(
    filter_cols: list[str], 
    observed_results: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Assess overfit risk based on number of filters tested.
    """
    count = len(filter_cols)
    risk = "LOW"
    if count > 10:
        risk = "MODERATE"
    if count > 20:
        risk = "HIGH"
        
    return {
        "filters_tested_count": count,
        "families_tested": ["EV_GT_0", "EV_GT_COST", "PROB_EV_COMBO", "TOP_QUANTILE"],
        "families_tested_count": 4,
        "parameter_count": count * 2, # Rough estimate
        "parameter_grid_size": count * 2,
        "multiple_testing_risk": risk,
        "evidence_classification": "EXPLORATORY_ONLY",
        "preregistration_allowed": False,
        "paper_live_allowed": False,
    }
