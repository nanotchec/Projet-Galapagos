from __future__ import annotations

def generate_recommendation(
    built_labels: list[str],
    version: str,
    improves_over_v1_46: bool,
    improves_stability: bool,
    improves_separability: bool
) -> dict:
    best_labels = built_labels if improves_over_v1_46 else []
    verdict = "MICROSTRUCTURE_REGIME_LABELS_ACTIONABLE_BUT_UNVALIDATED"
    next_step = "rerun regime diagnostics with selected microstructure labels"
    
    return {
        "version": version,
        "best_microstructure_regime_labels": best_labels,
        "weak_microstructure_regime_labels": [],
        "improves_over_v1_46_labels": improves_over_v1_46,
        "improves_stability_2026": improves_stability,
        "improves_separability_2026": improves_separability,
        "final_verdict": verdict,
        "recommended_next_step": next_step,
        "recommendation_status": "MICROSTRUCTURE_REGIME_LABEL_RECOMMENDATION_COMPLETED"
    }
