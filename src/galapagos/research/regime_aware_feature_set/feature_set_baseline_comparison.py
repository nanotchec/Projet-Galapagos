"""Baseline comparison for V1.44 feature sets."""
from __future__ import annotations

from typing import Any

def compare_to_baselines(
    eval_results: dict[str, Any]
) -> dict[str, Any]:
    """Compare V1.44 results against historical baselines."""
    
    # In V1.44, we compare stability scores.
    # v1_38_core_baseline is our primary baseline.
    
    baseline_res = eval_results.get("v1_38_core_baseline", {})
    baseline_stability = baseline_res.get("median_stability_score", 0.0)
    baseline_near_zero = baseline_stability < 1e-6
    
    comparisons = {}
    for name, res in eval_results.items():
        if name == "v1_38_core_baseline":
            continue
            
        stability = res.get("median_stability_score", 0.0)
        
        if baseline_near_zero:
            improvement = 0.0
            interpretation = "NOT_INTERPRETABLE_BASELINE_NEAR_ZERO"
        else:
            improvement = (stability / (baseline_stability + 1e-9)) - 1.0
            interpretation = "VALID"
            
        comparisons[name] = {
            "baseline_stability": baseline_stability,
            "set_stability": stability,
            "improvement_pct": float(improvement * 100) if not baseline_near_zero else None,
            "improvement_pct_valid": not baseline_near_zero,
            "improvement_interpretation": interpretation,
            "beats_baseline": stability > baseline_stability
        }
        
    valid_improvements = [c["improvement_pct"] for c in comparisons.values() if c["improvement_pct_valid"] and c["improvement_pct"] is not None]
    best_improvement = max(valid_improvements) if valid_improvements else 0.0
    
    return {
        "status": "BASELINE_COMPARISON_COMPLETE",
        "primary_baseline": "v1_38_core_baseline",
        "baseline_near_zero": baseline_near_zero,
        "comparisons": comparisons,
        "max_improvement_pct": float(best_improvement) if valid_improvements else None,
        "max_improvement_pct_valid": len(valid_improvements) > 0,
        "overall_improvement_detected": best_improvement > 0 and len(valid_improvements) > 0
    }
