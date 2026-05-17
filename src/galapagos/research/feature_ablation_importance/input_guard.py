"""Input guard for V1.45 research."""
from __future__ import annotations

from typing import Any

def validate_v1_45_inputs(
    v1_44_summary: dict[str, Any],
    v1_43_summary: dict[str, Any],
    v1_37_summary: dict[str, Any],
    safety_context: dict[str, Any]
) -> dict[str, Any]:
    """Verify that all prerequisite versions and safety flags are correct."""
    
    issues = []
    
    # 1. Version checks
    v1_44_v = v1_44_summary.get("version")
    if v1_44_v != "V1.44.4":
        issues.append(f"V1.44 summary version mismatch: {v1_44_v}")
    
    v1_43_v = v1_43_summary.get("version")
    if v1_43_v != "V1.43.4":
        issues.append(f"V1.43 summary version mismatch: {v1_43_v}")
        
    v1_37_v = v1_37_summary.get("universe_version") or v1_37_summary.get("version")
    if v1_37_v != "V1.37.2":
        issues.append(f"V1.37 summary version mismatch: {v1_37_v}")

    # 2. Verdict checks
    v1_44_verdict = v1_44_summary.get("final_verdict")
    if v1_44_verdict != "REGIME_AWARE_FEATURE_RESEARCH_INCONCLUSIVE":
        issues.append(f"Unexpected V1.44 verdict: {v1_44_verdict}")
        
    if v1_44_summary.get("consistency_check_status") != "REGIME_AWARE_FEATURE_REPORTS_CONSISTENT_RESEARCH_ONLY":
        issues.append(f"Inconsistent V1.44 status: {v1_44_summary.get('consistency_check_status')}")

    # 3. Safety checks
    if not safety_context.get("no_strategy_validated"):
        issues.append("Safety violation: no_strategy_validated must be True")
    if not safety_context.get("no_real_trading"):
        issues.append("Safety violation: no_real_trading must be True")
    if safety_context.get("holdout_executed"):
        issues.append("Safety violation: holdout_executed must be False")
        
    passed = len(issues) == 0
    status = "FEATURE_ABLATION_INPUT_GUARD_PASSED" if passed else "FEATURE_ABLATION_INPUT_GUARD_FAILED"
    
    return {
        "passed": passed,
        "status": status,
        "issues": issues,
        "regime_aware_feature_base_version": "V1.44.4",
        "regime_feature_base_version": "V1.43.4",
        "payoff_target_base_version": "V1.42.3",
        "payoff_failure_base_version": "V1.41",
        "ev_degradation_base_version": "V1.39",
        "canonical_base_version": "V1.37.2"
    }
