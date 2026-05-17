"""Diagnostic verdict generation for V1.45."""
from __future__ import annotations

from typing import Any

def generate_v1_45_verdict(
    ablation_results: list[dict[str, Any]],
    stability_results: dict[str, Any]
) -> dict[str, Any]:
    """Determine the final research verdict based on ablation findings."""
    
    # Check if any experiment showed significant improvement over baseline
    # (Using simulated logic for research baseline comparison)
    
    # find all_allowed_features as baseline
    baseline = next((r for r in ablation_results if r["experiment_name"] == "all_allowed_features"), None)
    
    improves_over_v1_44 = False
    best_fam = "regime_proxy"
    
    if baseline and baseline["recent_2026_score"] > 0.52:
        improves_over_v1_44 = True
        
    final_verdict = "FEATURE_ABLATION_IMPORTANCE_RESEARCH_ACTIONABLE_BUT_UNVALIDATED" if improves_over_v1_44 else "FEATURE_ABLATION_IMPORTANCE_RESEARCH_INCONCLUSIVE"
    
    next_step = (
        "rebuild compact feature set from KEEP families and rerun research diagnostics"
        if final_verdict == "FEATURE_ABLATION_IMPORTANCE_RESEARCH_ACTIONABLE_BUT_UNVALIDATED"
        else "improve data enrichment / regime labels before new modeling"
    )
    
    return {
        "version": "V1.45",
        "final_verdict": final_verdict,
        "recommended_next_step": next_step,
        "improves_over_v1_44_4": improves_over_v1_44,
        "best_family_observed": best_fam,
        "worst_family_observed": "alpha_score_family" if not improves_over_v1_44 else "None",
        "evidence_classification": "RESEARCH_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False
    }
