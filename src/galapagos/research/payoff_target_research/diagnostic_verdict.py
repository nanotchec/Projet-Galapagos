"""Formulate research verdict for payoff target research."""
from __future__ import annotations

from typing import Any

def formulate_verdict(results: dict[str, Any]) -> dict[str, Any]:
    """Decide on the final verdict of the V1.42 research."""
    beats_baseline = results.get("baseline_comparison", {}).get("beats_v1_40_1_target", False)
    noise_status = results.get("target_noise", {}).get("status")
    
    if beats_baseline:
        verdict = "PAYOFF_TARGET_RESEARCH_PROMISING_BUT_UNVALIDATED"
        recommendation = "harden best payoff target with ablations and diagnostics, still exploratory only"
    elif noise_status == "PAYOFF_TARGET_NOISE_HIGH":
        verdict = "PAYOFF_TARGET_RESEARCH_FAILED"
        recommendation = "return to feature engineering / regime-aware features before additional payoff objective research"
    else:
        verdict = "PAYOFF_TARGET_RESEARCH_RECENT_WINDOW_WEAK"
        recommendation = "return to feature engineering / regime-aware features before additional payoff objective research"
        
    return {
        "final_verdict": verdict,
        "recommended_next_step": recommendation,
        "evidence_classification": "EXPLORATORY_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True
    }
