"""Frequency reduction analysis."""
from __future__ import annotations

from typing import Any

import pandas as pd

from .evaluation import evaluate_rule_subset
from .selection_rules import cooldown, highest_score_per_period


def analyze_frequency(features: pd.DataFrame) -> dict[str, Any]:
    rules = {
        "cooldown_12h": cooldown("12h"),
        "cooldown_24h": cooldown("24h"),
        "highest_score_per_day": highest_score_per_period("1D"),
        "highest_score_per_week": highest_score_per_period("7D"),
    }
    rows: list[dict[str, Any]] = []
    for policy, policy_frame in features.groupby("policy"):
        for name, func in rules.items():
            mask = func(policy_frame)
            selected = policy_frame[mask]
            row = evaluate_rule_subset(policy_frame, selected, rule_name=name, policy=policy)
            row["cost_reduction_pct"] = 1.0 - row["selection_ratio"]
            rows.append(row)
    verdicts = ["NO_FREQUENCY_EDGE"]
    if any(r["net_mean_pnl_pct"] > 0 and r["selected_count"] >= 30 for r in rows):
        verdicts = ["LOW_FREQUENCY_FILTER_CANDIDATE", "FREQUENCY_REDUCTION_HELPFUL"]
    elif any(r["improvement_vs_all_candidates"] > 0 for r in rows):
        verdicts = ["FREQUENCY_REDUCTION_NOT_ENOUGH"]
    return {"rows": rows, "verdicts": verdicts}
