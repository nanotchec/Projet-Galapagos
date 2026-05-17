"""Policy comparison logic for trade evaluation."""
from __future__ import annotations

from typing import Any


def compare_policies(policy_metrics: dict[str, Any]) -> dict[str, Any]:
    """Compare multiple policies and determine the most effective one for this sample."""
    if not policy_metrics:
        return {"verdict": "NO_POLICIES_EVALUATED", "best_policy": None}

    best_policy = None
    max_pnl_after_cost = -999.0

    for name, metrics in policy_metrics.items():
        pnl = metrics.get("mean_pnl_after_cost_pct", -999.0)
        if pnl > max_pnl_after_cost:
            max_pnl_after_cost = pnl
            best_policy = name

    all_median_negative = True
    any_coverage_ok = False
    for _name, metrics in policy_metrics.items():
        if metrics.get("evaluated_ratio", 0.0) >= 0.2:
            any_coverage_ok = True
        if metrics.get("median_pnl_after_cost_pct", 0.0) > 0:
            all_median_negative = False

    # Determine verdict
    if not any_coverage_ok:
        verdict = "TRADE_LEDGER_INTRABAR_SAMPLE_TOO_SHORT"
        policy_comparison_valid = False
    elif max_pnl_after_cost <= 0:
        verdict = "ALL_POLICIES_NEGATIVE_AFTER_COSTS"
        policy_comparison_valid = True
    elif best_policy == "atr_proxy":
        verdict = "ATR_POLICY_IMPROVES_EXITS"
        policy_comparison_valid = True
    elif best_policy == "horizon_only":
        verdict = "HORIZON_ONLY_BETTER_THAN_TPSL"
        policy_comparison_valid = True
    else:
        verdict = "FIXED_POLICY_SUFFICIENT"
        policy_comparison_valid = True

    warnings = []
    if all_median_negative:
        warnings.append("MEDIAN_PNL_NEGATIVE_ALL_POLICIES")

    return {
        "best_policy": best_policy if policy_comparison_valid else f"observed_only_{best_policy}",
        "best_mean_pnl_after_cost_pct": float(max_pnl_after_cost),
        "verdict": verdict,
        "policy_comparison_valid": policy_comparison_valid,
        "warnings": warnings,
        "comparison_count": len(policy_metrics),
        "all_negative": max_pnl_after_cost <= 0,
        "all_median_negative": all_median_negative,
    }
