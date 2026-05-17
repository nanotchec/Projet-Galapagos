"""Run cost-aware filter sweeps."""
from __future__ import annotations

from typing import Any

import pandas as pd

from .evaluation import evaluate_rule_subset
from .random_baselines import observed_percentile, random_same_count_baseline
from .selection_rules import SelectionRule


def run_filter_sweep(
    features: pd.DataFrame,
    rules: list[SelectionRule],
    *,
    policies: list[str],
    iterations: int = 500,
    seed: int = 2401,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sweep: list[dict[str, Any]] = []
    random_rows: list[dict[str, Any]] = []
    for policy in policies:
        policy_frame = features[features["policy"] == policy].copy()
        for index, rule in enumerate(rules):
            mask = rule.apply(policy_frame).reindex(policy_frame.index).fillna(False)
            selected = policy_frame[mask].copy()
            random_stats = random_same_count_baseline(
                policy_frame,
                len(selected),
                iterations=iterations,
                seed=seed + index,
            )
            metrics = evaluate_rule_subset(
                policy_frame,
                selected,
                rule_name=rule.name,
                policy=policy,
                random_stats=random_stats,
            )
            metrics["rule_family"] = rule.family
            metrics["description"] = rule.description
            metrics["causal"] = rule.causal
            metrics["used_columns"] = list(rule.used_columns)
            sweep.append(metrics)
            random_rows.append(
                {
                    "policy": policy,
                    "rule_name": rule.name,
                    "causal": rule.causal,
                    "used_columns": list(rule.used_columns),
                    "selected_count": len(selected),
                    "observed_net_mean": metrics["net_mean_pnl_pct"],
                    **{k: v for k, v in random_stats.items() if k != "samples"},
                    "percentile_of_observed": observed_percentile(
                        metrics["net_mean_pnl_pct"], random_stats.get("samples", [])
                    ),
                    "p_value_estimate": 1.0
                    - observed_percentile(
                        metrics["net_mean_pnl_pct"], random_stats.get("samples", [])
                    ),
                    "beats_random_p95": metrics["beats_random_p95"],
                    "verdict": _random_verdict(metrics),
                }
            )
    return sweep, random_rows


def _random_verdict(metrics: dict[str, Any]) -> list[str]:
    if metrics["selected_count"] < 30:
        return ["SAMPLE_TOO_SMALL"]
    if metrics["beats_random_p95"]:
        return ["BEATS_RANDOM_P95_PROMISING_BUT_UNVALIDATED"]
    if metrics["beats_random_mean"]:
        return ["BEATS_RANDOM_MEAN_ONLY"]
    return ["DOES_NOT_BEAT_RANDOM"]
