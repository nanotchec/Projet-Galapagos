"""Input guard for V1.43 diagnostic."""
from __future__ import annotations

from typing import Any

def validate_diagnostic_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    """Verify base versions and safety status."""
    payoff_summary = inputs["payoff_summary"]
    payoff_failure_summary = inputs["payoff_failure_summary"]
    ev_degradation_summary = inputs["ev_degradation_summary"]
    canonical_summary = inputs["canonical_summary"]
    
    issues = []
    
    if payoff_summary.get("version") != "V1.42.3":
        issues.append(f"payoff_target_base mismatch: {payoff_summary.get('version')} != V1.42.3")
    if payoff_failure_summary.get("version") != "V1.41":
        issues.append(f"payoff_failure_base mismatch: {payoff_failure_summary.get('version')} != V1.41")
    if ev_degradation_summary.get("version") != "V1.39":
        issues.append(f"ev_degradation_base mismatch: {ev_degradation_summary.get('version')} != V1.39")
    if (canonical_summary.get("version") or canonical_summary.get("universe_version")) != "V1.37.2":
        issues.append(f"canonical_base mismatch: {canonical_summary.get('version') or canonical_summary.get('universe_version')} != V1.37.2")
    
    # Strict null check
    canon_v = canonical_summary.get("version") or canonical_summary.get("universe_version")
    if not canon_v:
        issues.append("canonical_base_version is null")
        
    if payoff_summary.get("final_verdict") != "PAYOFF_TARGET_RESEARCH_RECENT_WINDOW_WEAK":
        issues.append("V1.42.3 verdict mismatch")
    if payoff_failure_summary.get("final_verdict") != "PAYOFF_OBJECTIVE_FAILURE_MULTI_FACTOR":
        issues.append("V1.41 verdict mismatch")
    if ev_degradation_summary.get("final_verdict") != "EV_DEGRADATION_MULTI_FACTOR":
        issues.append("V1.39 verdict mismatch")

    # Safety
    if payoff_summary.get("no_strategy_validated") is not True:
        issues.append("V1.42.3 safety violation")
    if payoff_summary.get("no_real_trading") is not True:
        issues.append("V1.42.3 safety violation (real trading)")

    return {
        "status": "REGIME_FEATURE_INPUT_GUARD_PASSED" if not issues else "REGIME_FEATURE_INPUT_GUARD_FAILED",
        "issues": issues,
        "payoff_target_base_version": payoff_summary.get("version"),
        "payoff_failure_base_version": payoff_failure_summary.get("version"),
        "ev_degradation_base_version": ev_degradation_summary.get("version"),
        "canonical_base_version": canonical_summary.get("version") or canonical_summary.get("universe_version"),
        "canonical_base_version_present": bool(canonical_summary.get("version") or canonical_summary.get("universe_version")),
        "canonical_summary_loaded": bool(canonical_summary),
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
    }
