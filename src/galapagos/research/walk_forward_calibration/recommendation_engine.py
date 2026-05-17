from __future__ import annotations

from typing import Any


def generate_v1_31_recommendation(summary: dict[str, Any]) -> dict[str, Any]:
    """
    Generate V1.31.1 recommendations.
    """
    ece_improves = summary.get("calibration_improves_ece", False)
    brier_improves = summary.get("calibration_improves_brier", False)
    stable = summary.get("calibration_stable_2026") is True
    
    if ece_improves and brier_improves and stable:
        verdict = "WALK_FORWARD_CALIBRATION_PROMISING_RESEARCH_ONLY"
        next_step = "V1.32 EV-net filter research using calibrated probabilities"
    elif not stable:
        verdict = "WALK_FORWARD_CALIBRATION_FAILED_RECENT_WINDOW"
        next_step = "Improve calibrator robustness or underlying features"
    else:
        verdict = "RAW_PROBABILITIES_REMAIN_UNUSABLE"
        next_step = "Improve alpha model/features before threshold research"
        
    return {
        "final_verdict": verdict,
        "recommended_next_step": next_step,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_money_deployment": True,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True
    }
