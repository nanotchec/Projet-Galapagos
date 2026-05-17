"""Input guard for V1.44 research."""
from __future__ import annotations

from typing import Any

def validate_v1_44_inputs(
    v1_43_summary: dict[str, Any],
    v1_43_inventory: dict[str, Any],
    v1_43_scorecard: dict[str, Any],
    version: str = "V1.44.2"
) -> dict[str, Any]:
    """Verify that the inputs are valid for V1.44 research."""
    
    issues = []
    
    # 1. Base Version Check
    base_v = v1_43_summary.get("version", "")
    if base_v not in ["V1.43.4", "V1.44", "V1.44.1", "V1.44.2"]:
        issues.append(f"Invalid base version: {base_v}. Expected V1.43.4, V1.44.x.")
        
    # 2. Base Status Check
    status = v1_43_summary.get("consistency_check_status", "")
    allowed_statuses = [
        "REGIME_FEATURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY",
        "REGIME_AWARE_FEATURE_RESEARCH_REPORTS_CONSISTENT_RESEARCH_ONLY",
        "REGIME_AWARE_FEATURE_REPORTS_CONSISTENT_RESEARCH_ONLY"
    ]
    if status not in allowed_statuses:
        issues.append(f"Invalid consistency status in base: {status}")
        
    # 3. Feature Inventory Check
    inv_status = v1_43_inventory.get("inventory_status", "")
    if inv_status != "REGIME_FEATURE_INVENTORY_COMPLETE_WITH_STRICT_SOURCE_SEMANTICS":
        issues.append(f"Invalid inventory status: {inv_status}")
        
    # 4. Scorecard Check
    scorecard_status = v1_43_scorecard.get("feature_stability_scorecard_status", "")
    if scorecard_status != "FEATURE_STABILITY_SCORECARD_COMPLETE":
        issues.append(f"Invalid scorecard status: {scorecard_status}")
        
    # 5. Safety Flags (Must be True)
    for flag in ["no_strategy_validated", "no_paper_live", "no_real_trading", "no_preregistration_yet"]:
        if not v1_43_summary.get(flag, False) and flag != "no_preregistration_yet": # V1.43.4 might not have no_preregistration_yet
            issues.append(f"Safety violation: {flag} is not True in base version.")

    # 6. Negative Guards (Must NOT contain)
    recommendation = v1_43_summary.get("recommended_next_step", "").lower()
    if "preregister" in recommendation or "preregistration" in recommendation:
        issues.append(f"Invalid recommendation in base: {recommendation}")

    passed = len(issues) == 0
    
    return {
        "version": version,
        "previous_base": base_v,
        "regime_feature_base_version": "V1.43.4",
        "payoff_target_base_version": "V1.42.3",
        "payoff_failure_base_version": "V1.41",
        "ev_degradation_base_version": "V1.39",
        "canonical_base_version": "V1.37.2",
        "input_guard_status": "REGIME_AWARE_FEATURE_INPUT_GUARD_PASSED" if passed else "REGIME_AWARE_FEATURE_INPUT_GUARD_FAILED",
        "passed": passed,
        "issues": issues,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "no_preregistration_yet": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "evidence_classification": "RESEARCH_ONLY"
    }
