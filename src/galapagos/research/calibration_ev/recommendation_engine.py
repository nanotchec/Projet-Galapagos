from __future__ import annotations

from typing import Any


def generate_v1_30_recommendations(summary: dict[str, Any]) -> dict[str, Any]:
    """
    Generate next steps based on research results.
    """
    verdict = "RAW_PROBABILITY_THRESHOLD_NOT_READY"
    recommendations = [
        "V1.31 calibrate probabilities on walk-forward validation only",
        "V1.31 build causal regime matrix",
        "V1.31 improve cost model",
        "V1.31 build EV-net candidate filters"
    ]
    
    if (
        summary.get("calibration_global_status") == "CALIBRATION_ACCEPTABLE_EXPLORATORY"
        and summary.get("ev_proxy_status") == "EV_PROXY_RESEARCH_FOUNDATION_READY"
    ):
        verdict = "EV_PROXY_RESEARCH_FOUNDATION_READY"
            
    return {
        "final_verdict": verdict,
        "recommended_next_steps": recommendations,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_money_deployment": True,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True
    }
