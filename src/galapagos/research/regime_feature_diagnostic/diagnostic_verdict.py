"""Final diagnostic verdict for V1.43."""
from __future__ import annotations

from typing import Any

def determine_diagnostic_verdict(results: dict[str, Any]) -> dict[str, Any]:
    """Analyze all diagnostic components to identify the primary failure drivers."""
    shift = results["feature_shift"]
    decay = results["predictive_power"]
    scorecard = results["stability_scorecard"]
    
    primary_drivers = []
    secondary_drivers = []
    
    if shift.get("severe_shift_count", 0) > 20:
        primary_drivers.append("MASSIVE_FEATURE_DISTRIBUTION_SHIFT_2026")
    if decay.get("sign_flip_count", 0) > 10:
        primary_drivers.append("PREDICTIVE_POWER_DECAY_WITH_SIGN_FLIPS")
    if results["regime_coverage"].get("regime_coverage_status") == "REGIME_COVERAGE_SHIFT_2026":
        secondary_drivers.append("REGIME_DISTRIBUTION_SHIFT")
    if results["regime_definition"].get("regime_definition_status") == "REGIME_DEFINITION_TOO_COARSE":
        secondary_drivers.append("REGIME_DEFINITION_INSUFFICIENT_GRANULARITY")
        
    verdict = "REGIME_FEATURE_FAILURE_MULTI_FACTOR"
    if len(primary_drivers) == 1:
        verdict = "REGIME_FEATURE_FAILURE_DRIVER_IDENTIFIED"
    elif not primary_drivers and not secondary_drivers:
        verdict = "REGIME_FEATURE_DIAGNOSTIC_INCONCLUSIVE"
        
    next_step = "research regime-aware feature set with stability constraints"
    if "REGIME_DEFINITION_INSUFFICIENT_GRANULARITY" in secondary_drivers:
        next_step = "improve regime definition before feature engineering"
        
    return {
        "final_verdict": verdict,
        "primary_feature_failure_driver": primary_drivers[0] if primary_drivers else "MULTI_FACTOR",
        "secondary_feature_failure_drivers": secondary_drivers,
        "recommended_next_step": next_step,
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True
    }
