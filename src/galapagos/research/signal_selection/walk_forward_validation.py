"""Walk-forward checks for signal selection filters."""
from __future__ import annotations

from typing import Any

import pandas as pd

from .evaluation import evaluate_rule_subset
from .random_baselines import random_same_count_baseline
from .selection_rules import SelectionRule, build_default_rules

WINDOWS = [
    ("2024_H1", "2024-01-01", "2024-07-01"),
    ("2024_H2", "2024-07-01", "2025-01-01"),
    ("2025_H1", "2025-01-01", "2025-07-01"),
    ("2025_H2", "2025-07-01", "2026-01-01"),
    ("2026_YTD", "2026-01-01", "2027-01-01"),
]


def run_walk_forward_validation(
    features: pd.DataFrame,
    *,
    rules: list[SelectionRule] | None = None,
    policies: list[str] | None = None,
    primary_rule_name: str = "low_frequency_strict_score",
    primary_policy: str = "horizon_only",
    top_rule_names: list[str] | None = None,
    iterations: int = 500,
    seed: int = 2411,
) -> dict[str, Any]:
    rules = rules or build_default_rules()
    rule_map = {rule.name: rule for rule in rules if rule.causal}
    if top_rule_names is None:
        top_rule_names = [primary_rule_name]
    if primary_rule_name not in top_rule_names:
        top_rule_names.insert(0, primary_rule_name)
    policy_list = policies or [primary_policy]
    frame = features.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    rows: list[dict[str, Any]] = []
    for policy in policy_list:
        policy_frame = frame[frame["policy"] == policy].copy()
        for rule_name in top_rule_names:
            rule = rule_map.get(rule_name)
            if rule is None:
                continue
            for window_name, start, end in WINDOWS:
                start_ts = pd.Timestamp(start, tz="UTC")
                end_ts = pd.Timestamp(end, tz="UTC")
                window_frame = policy_frame[
                    (policy_frame["timestamp"] >= start_ts)
                    & (policy_frame["timestamp"] < end_ts)
                ].copy()
                selected = _apply_rule(rule, window_frame)
                random_stats = random_same_count_baseline(
                    window_frame,
                    len(selected),
                    iterations=iterations,
                    seed=seed + len(rows),
                )
                metrics = evaluate_rule_subset(
                    window_frame,
                    selected,
                    rule_name=rule.name,
                    policy=policy,
                    random_stats=random_stats,
                )
                rows.append(
                    {
                        "window": window_name,
                        "start": start,
                        "end": end,
                        "sample_warning": _sample_warning(metrics["selected_count"]),
                        **metrics,
                    }
                )
    primary_rows = [
        row
        for row in rows
        if row["policy"] == primary_policy and row["rule_name"] == primary_rule_name
    ]
    verdict = _walk_forward_verdict(primary_rows)
    return {
        "windows": [item[0] for item in WINDOWS],
        "rows": rows,
        "primary_rule": primary_rule_name,
        "primary_policy": primary_policy,
        "walk_forward_verdict": verdict,
        "low_frequency_strict_score_remains_promising": verdict
        in {"WALK_FORWARD_PASS_STRONG", "PROMISING_BUT_NEEDS_NEXT_VALIDATION"},
    }


def _apply_rule(rule: SelectionRule, frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    mask = rule.apply(frame).reindex(frame.index).fillna(False)
    return frame[mask].copy()


def _sample_warning(selected_count: int) -> str | None:
    if selected_count < 30:
        return "SAMPLE_TOO_SMALL"
    if selected_count < 100:
        return "LOW_CONFIDENCE_SAMPLE"
    return None


def _walk_forward_verdict(primary_rows: list[dict[str, Any]]) -> str:
    if not primary_rows:
        return "WALK_FORWARD_SAMPLE_TOO_SMALL"
    enough_rows = [row for row in primary_rows if row["selected_count"] >= 30]
    if len(enough_rows) < 2:
        return "WALK_FORWARD_SAMPLE_TOO_SMALL"
    positive = sum(1 for row in enough_rows if row["net_mean_pnl_pct"] > 0)
    beats_p95 = sum(1 for row in enough_rows if row["beats_random_p95"])
    recent_rows = [row for row in enough_rows if row["window"] in {"2025_H2", "2026_YTD"}]
    recent_fail = any(row["net_mean_pnl_pct"] <= 0 for row in recent_rows)
    if positive == len(enough_rows) and beats_p95 >= max(1, len(enough_rows) - 1):
        return "WALK_FORWARD_PASS_STRONG"
    if recent_fail:
        return "WALK_FORWARD_FAILS_RECENT_WINDOW"
    if positive >= max(1, len(enough_rows) // 2):
        return "PROMISING_BUT_NEEDS_NEXT_VALIDATION"
    return "WALK_FORWARD_MIXED"
