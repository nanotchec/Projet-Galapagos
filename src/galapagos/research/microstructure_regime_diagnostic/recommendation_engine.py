"""Recommend next steps based on microstructure regime diagnostics V1.49."""
from __future__ import annotations
from typing import Any

def generate_recommendations(diagnostic_results: dict[str, Any]) -> dict[str, Any]:
    """Decide on next research phase."""
    explaining = diagnostic_results.get("failure_2026_analysis", {}).get("explaining_regimes", [])
    
    if explaining:
        rec = "rerun feature ablation with selected microstructure regime labels"
        reason = "Microstructure regimes successfully isolated 2026 failure slices."
    else:
        rec = "improve microstructure data coverage before further regime diagnostics"
        reason = "Current labels did not significantly improve 2026 failure explanation."
        
    return {
        "recommended_next_step": rec,
        "recommendation_reason": reason,
        "selected_for_next_phase": diagnostic_results.get("labels_used", [])
    }
