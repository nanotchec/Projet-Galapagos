"""Verdict logic for payoff-objective failure diagnostics."""
from __future__ import annotations

from typing import Any


def build_failure_diagnostic_verdict(summary: dict[str, Any]) -> dict[str, Any]:
    if summary.get("candidate_rebuild_status") == "PAYOFF_OBJECTIVE_CANDIDATE_REBUILD_MISMATCH":
        return {
            "final_verdict": "PAYOFF_OBJECTIVE_FAILURE_INCONCLUSIVE",
            "recommended_next_step": "fix candidate rebuild and report alignment before further diagnostic work",
        }
    drivers = [
        summary.get("score_decile_status"),
        summary.get("label_noise_status"),
        summary.get("downside_miss_status"),
        summary.get("feature_shift_status"),
        summary.get("regime_transfer_status"),
        summary.get("cost_vs_gross_status"),
        summary.get("ranking_quality_status"),
    ]
    if summary.get("ranking_quality_status") == "RANKING_QUALITY_DEGRADED_2026":
        primary = "RANKING_QUALITY_DEGRADED_2026"
        next_step = "improve feature stability and ranking objective before further model research"
    elif summary.get("cost_vs_gross_status") == "PAYOFF_OBJECTIVE_EDGE_NEGATIVE_BEFORE_COSTS":
        primary = "PAYOFF_OBJECTIVE_EDGE_NEGATIVE_BEFORE_COSTS"
        next_step = "improve label horizon and payoff-aware target definition before more model research"
    else:
        primary = "PAYOFF_OBJECTIVE_FAILURE_MULTI_FACTOR"
        next_step = "improve downside-aware labels and regime-aware features before more model research"
    return {
        "primary_failure_driver": primary,
        "secondary_failure_drivers": [driver for driver in drivers if driver and driver != primary],
        "final_verdict": "PAYOFF_OBJECTIVE_FAILURE_MULTI_FACTOR",
        "recommended_next_step": next_step,
    }
