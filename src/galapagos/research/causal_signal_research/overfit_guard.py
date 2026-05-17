from __future__ import annotations

from typing import Any

def calculate_overfit_risk(
    n_variants: int, 
    n_families: int,
    baselines_available: bool = True
) -> dict[str, Any]:
    """Assess risk based on search space size and baseline availability."""
    
    risk = "LOW"
    if n_variants > 50:
        risk = "HIGH"
    elif n_variants > 20:
        risk = "MODERATE"
        
    if not baselines_available:
        classification = "RESEARCH_INCOMPLETE"
    else:
        classification = "EXPLORATORY_ONLY"
        
    return {
        "number_of_filter_variants_tested": n_variants,
        "number_of_families_tested": n_families,
        "multiple_testing_risk": risk,
        "baselines_available": baselines_available,
        "evidence_classification": classification,
        "missing_baseline_penalty": not baselines_available
    }
