"""Overfit guard for payoff-aware objective research."""
from __future__ import annotations

from typing import Any


def build_overfit_guard(candidate_rows: list[dict[str, Any]], split_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a conservative overfit risk assessment."""
    candidates_tested = len(candidate_rows)
    targets_tested = len({row.get("target_column") for row in split_rows if row.get("target_column")})
    metric_count = len(split_rows) * 6
    if candidates_tested <= 4:
        risk = "LOW"
    elif candidates_tested <= 8:
        risk = "MODERATE"
    else:
        risk = "HIGH"
    return {
        "candidates_tested_count": candidates_tested,
        "targets_tested_count": targets_tested,
        "metric_count": metric_count,
        "multiple_testing_risk": risk,
        "overfit_guard_status": f"PAYOFF_OBJECTIVE_OVERFIT_RISK_{risk}",
        "evidence_classification": "EXPLORATORY_ONLY",
        "preregistration_allowed": False,
        "paper_live_allowed": False,
        "no_strategy_validated": True,
    }
