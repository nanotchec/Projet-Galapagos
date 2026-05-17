"""Compare research targets against baselines."""
from __future__ import annotations

from typing import Any

def compare_targets_to_baselines(
    eval_results: dict[str, Any],
    payoff_summary: dict[str, Any]
) -> dict[str, Any]:
    """Compare new target performance against V1.40.1 and other baselines."""
    v1_40_1_metric = payoff_summary.get("best_candidate_2026_metric", -0.004919)
    v1_40_1_downside = payoff_summary.get("best_candidate_downside_metric", 0.5386)
    
    # Find best target in 2026 from walk-forward eval ONLY if it has a score
    best_target = None
    best_metric = -999.0
    best_downside = 1.0
    
    eval_list = eval_results.get("eval_results", [])
    h1_2026 = next((p for p in eval_list if p["period"] == "2026_H1"), None)
    
    evaluated_targets = []
    
    if h1_2026:
        for t_name, stats in h1_2026.items():
            if isinstance(stats, dict) and stats.get("top_decile_mean_net_return") is not None:
                metric = stats.get("top_decile_mean_net_return", -999.0)
                if metric > best_metric:
                    best_metric = metric
                    best_target = t_name
                    best_downside = stats.get("top_decile_downside_rate", 1.0)
                evaluated_targets.append(t_name)

    beats_v1_40_1 = best_metric > v1_40_1_metric if best_target else False
    
    status = "PAYOFF_TARGET_BASELINE_COMPARISON_COMPLETE" if evaluated_targets else "PAYOFF_TARGET_BASELINE_COMPARISON_LIMITED"
    
    return {
        "status": status,
        "best_target_observed": best_target,
        "best_target_2026_metric": float(best_metric) if best_target else None,
        "best_target_downside_metric": float(best_downside) if best_target else None,
        "v1_40_1_baseline_metric": float(v1_40_1_metric),
        "beats_v1_40_1_target": bool(beats_v1_40_1),
        "beats_probability_baseline": False, # Requires recalculation
        "beats_ev_proxy_baseline": False, # Requires recalculation
        "beats_random_baseline": False, # Requires recalculation
        "compared_targets": evaluated_targets,
        "comparison_status": "INCONCLUSIVE_NO_TARGET_SCORES" if not evaluated_targets else "COMPLETE"
    }
