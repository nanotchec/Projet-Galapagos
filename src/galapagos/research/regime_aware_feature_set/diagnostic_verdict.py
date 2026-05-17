"""Diagnostic verdict for V1.44 research."""
from __future__ import annotations

from typing import Any

def generate_v1_44_verdict(
    audit_results: dict[str, Any],
    comparison_results: dict[str, Any],
    overfit_results: dict[str, Any],
    source_contract_passed: bool = True,
    metrics_available: bool = False
) -> dict[str, Any]:
    """Determine the final verdict for V1.44 research."""
    
    overall_improvement = comparison_results.get("overall_improvement_detected", False)
    all_audit_passed = audit_results.get("all_passed", False)
    overfit_risk = overfit_results.get("overfit_risk_level", "UNKNOWN")
    
    if not source_contract_passed:
        verdict = "REGIME_AWARE_FEATURE_RESEARCH_BLOCKED_BY_SOURCE_CONTRACT"
        recommendation = "fix source contract / remove forbidden features before further research"
    elif not all_audit_passed:
        verdict = "REGIME_AWARE_FEATURE_RESEARCH_AUDIT_FAILED"
        recommendation = "fix feature set definitions and remove unknown columns"
    elif not metrics_available:
        verdict = "REGIME_AWARE_FEATURE_RESEARCH_INCONCLUSIVE"
        recommendation = "run stricter ablation and causal feature importance, then rerun feature-set research"
    elif overall_improvement and overfit_risk != "HIGH":
        verdict = "REGIME_AWARE_FEATURE_RESEARCH_PROMISING_BUT_UNVALIDATED"
        recommendation = "run stricter ablation and causal feature importance, then rerun feature-set research"
    elif overall_improvement and overfit_risk == "HIGH":
        verdict = "REGIME_AWARE_FEATURE_RESEARCH_IMPROVEMENT_UNCERTAIN_OVERFIT_RISK"
        recommendation = "reduce candidate search space and re-evaluate feature builders"
    else:
        verdict = "REGIME_AWARE_FEATURE_RESEARCH_INCONCLUSIVE"
        recommendation = "run stricter ablation and causal feature importance, then rerun feature-set research"
        
    return {
        "final_verdict": verdict,
        "recommended_next_step": recommendation,
        "overall_improvement_detected": overall_improvement,
        "audit_passed": all_audit_passed,
        "source_contract_passed": source_contract_passed,
        "metrics_available": metrics_available,
        "overfit_risk": overfit_risk,
        "evidence_classification": "RESEARCH_ONLY",
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "no_preregistration_yet": True
    }
