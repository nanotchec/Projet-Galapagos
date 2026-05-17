from __future__ import annotations

from typing import Any

def generate_diagnostic_recommendation(diagnostics: dict[str, Any]) -> dict[str, Any]:
    """Synthesize results and recommend next steps."""
    
    recent_fail = diagnostics.get("recent_window_diagnostic", {}).get("recent_degradation_confirmed", False)
    regime_fail = diagnostics.get("regime_dependency", {}).get("regime_dependency_status") == "BULL_REGIME_DEPENDENT"
    cost_fail = diagnostics.get("cost_drag", {}).get("cost_drag_status") == "EDGE_KILLED_BY_COSTS_RECENT"
    
    verdict = "DIAGNOSTIC_INCONCLUSIVE"
    recommended = "continue exploratory research"
    do_not_progress = True
    
    if recent_fail and regime_fail:
        verdict = "RECENT_DEGRADATION_AND_REGIME_DEPENDENCY_CONFIRMED"
        recommended = "improve alpha features or research causal regime-aware filters"
    elif recent_fail:
        verdict = "RECENT_DEGRADATION_CONFIRMED_ON_CLEAN_SELECTION_FRAME"
        recommended = "deep dive into 2026 H1 market structure"
    elif regime_fail:
        verdict = "REGIME_DEPENDENT_FILTER_ONLY"
        recommended = "research diversification across regimes"
        
    if cost_fail:
        recommended += " + cost reduction research"
        
    return {
        "final_diagnostic_verdict": verdict,
        "recommended_next_step": recommended,
        "do_not_progress_to_v1_30": do_not_progress,
        "evidence_classification": "EXPLORATORY_ONLY",
        "ready_for_reviewer": False,
        "no_real_trading": True
    }
