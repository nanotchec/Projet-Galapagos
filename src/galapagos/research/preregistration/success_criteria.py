from __future__ import annotations

from typing import Any


def get_success_criteria() -> dict[str, Any]:
    """Define fixed success and failure criteria for signal validation."""
    return {
        "minimal_requirements": {
            "selected_count": ">= 60",
            "mean_net_pnl_after_cost_pct": "> 0",
            "median_net_pnl_after_cost_pct": ">= 0",
            "total_net_pnl_pct": "> 0",
            "profit_factor": "> 1.2",
            "beats_monthly_count_random_p95": True,
            "beats_same_count_random_p95": True,
            "top_10_trades_contribution": "< 0.50",
            "top_month_contribution": "< 0.50",
            "recent_window_net_mean": "> 0",
            "cost_sensitivity_positive_at_0_30": True,
            "cost_sensitivity_not_collapsed_at_0_50": True,
            "leakage_audit_passed": True
        },
        "failure_triggers": {
            "recent_window_negative": True,
            "sample_size_too_small": "count < 30",
            "extreme_trade_concentration": "top_10 > 0.60",
            "extreme_temporal_concentration": "top_month > 0.60",
            "fails_monthly_count_random_p95": True,
            "fails_same_count_random_p95": True,
            "cost_0_30_negative": True,
            "cost_0_50_extreme_loss": True,
            "leakage_detected": True,
            "protocol_violation": [
                "filter_changed", "policy_changed", 
                "data_source_changed", "metrics_changed"
            ]
        },
        "verdict_logic": (
            "All minimal requirements must be passed; "
            "no failure triggers must be active."
        )
    }
