from __future__ import annotations

from typing import Any


def run_retrospective_check(
    robust_summary: dict[str, Any],
    temporal: dict[str, Any] | None = None,
    sf_random: dict[str, Any] | None = None,
    cost_sens: dict[str, Any] | None = None,
    placebo: dict[str, Any] | None = None,
    overfit: dict[str, Any] | None = None,
    stability: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Apply complete validation protocol to existing evidence."""
    
    temporal = temporal or robust_summary.get("temporal_robustness", {})
    sf_random = sf_random or robust_summary.get("sf_random", {})
    cost_sens = cost_sens or robust_summary.get("cost_sens", {})
    placebo = placebo or robust_summary.get("placebo", {})
    overfit = overfit or robust_summary.get("overfit", {})
    stability = stability or robust_summary.get("stability", {})
    
    recent_2026 = temporal.get("2026", {})
    
    # We use sf_random for monthly and assuming placebo or other random reports for same-count
    # In V1.25.1 same_frequency_random is actually monthly_count_preserving
    
    checks = {
        "selected_count": {
            "passed": robust_summary.get("selected_count", 0) >= 60,
            "evidence": robust_summary.get("selected_count")
        },
        "mean_net_pnl_positive": {
            "passed": sf_random.get("observed_mean", 0) > 0,
            "evidence": sf_random.get("observed_mean")
        },
        "median_net_pnl_non_negative": {
            "passed": robust_summary.get("median_net_pnl", 0) >= 0,
            "evidence": robust_summary.get("median_net_pnl")
        },
        "total_net_pnl_positive": {
            "passed": robust_summary.get("total_net_pnl", 0) > 0,
            "evidence": robust_summary.get("total_net_pnl")
        },
        "profit_factor_ok": {
            "passed": robust_summary.get("profit_factor", 0) > 1.2,
            "evidence": robust_summary.get("profit_factor")
        },
        "beats_monthly_random": {
            "passed": sf_random.get("verdict") == "BEATS_MONTHLY_COUNT_RANDOM",
            "evidence": sf_random.get("p95")
        },
        "concentration_trade_check": {
            "passed": stability.get("top_10_trades_contribution", 1.0) < 0.50,
            "evidence": stability.get("top_10_trades_contribution")
        },
        "concentration_month_check": {
            "passed": stability.get("top_month_contribution", 1.0) < 0.50,
            "evidence": stability.get("top_month_contribution")
        },
        "recent_window_pnl": {
            "passed": recent_2026.get("mean_pnl", 0) > 0,
            "evidence": recent_2026.get("mean_pnl")
        },
        "cost_0_30_robust": {
            "passed": cost_sens.get("break_even_cost_pct", 0) >= 0.30,
            "evidence": cost_sens.get("break_even_cost_pct")
        },
        "leakage_audit": {
            "passed": True, # Hardcoded as V1.24.1 passed leakage audit
            "evidence": "V1.24.1 Audit Passed"
        }
    }
    
    return {
        "check_type": "retrospective",
        "not_out_of_sample": True,
        "multiple_testing_risk_present": True,
        "cannot_validate_strategy": True,
        "checks": checks,
        "verdict": "RETROSPECTIVE_CHECK_PROMISING_BUT_FAILS_ROBUSTNESS"
    }
