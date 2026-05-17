from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import pandas as pd


def analyze_signal_quality(
    labels: pd.DataFrame,
    signals: pd.DataFrame,
    random_returns: list[float] | None = None,
    cost_threshold: float = 0.003,
) -> dict[str, Any]:
    groups: dict[str, list[int]] = defaultdict(list)
    for _, signal in signals.iterrows():
        group_name = str(signal.get("group", signal.get("source", "unknown")))
        groups[group_name].append(int(signal["index"]))
    output = {
        "groups": {
            group: _summarize_indexes(labels, indexes, cost_threshold)
            for group, indexes in sorted(groups.items())
        },
        "warnings": [],
    }
    if random_returns is not None:
        random_mean = sum(random_returns) / len(random_returns) if random_returns else 0.0
        for summary in output["groups"].values():
            summary["percentage_beating_random_baseline"] = (
                1.0 if summary["mean_forward_return_6bar"] > random_mean else 0.0
            )
    total = len(signals)
    if total < 30:
        output["warnings"].append("sample_below_30")
    if total < 100:
        output["warnings"].append("low_confidence_sample_below_100")
    output["verdicts"] = signal_quality_verdicts(output)
    return output


def signal_quality_verdicts(analysis: dict[str, Any]) -> list[str]:
    verdicts = []
    groups = analysis.get("groups", {})
    best = max(
        (group.get("cost_adjusted_expected_return", 0.0) for group in groups.values()),
        default=0.0,
    )
    if best <= 0:
        verdicts.append("NO_EDGE_DETECTED")
    elif best < 0.003:
        verdicts.append("WEAK_EDGE_BEFORE_COSTS")
    if "low_confidence_sample_below_100" in analysis.get("warnings", []):
        verdicts.append("NEED_MORE_DATA")
    return verdicts or ["READY_FOR_LONG_HISTORY_RESEARCH"]


def _summarize_indexes(labels: pd.DataFrame, indexes: list[int], cost_threshold: float) -> dict:
    valid = [index for index in indexes if 0 <= index < len(labels)]
    returns = {
        horizon: [
            float(labels.iloc[index][f"forward_return_{horizon}bar"])
            for index in valid
            if pd.notna(labels.iloc[index].get(f"forward_return_{horizon}bar"))
        ]
        for horizon in (1, 3, 6, 12)
    }
    mfe = [
        float(labels.iloc[index]["max_favorable_excursion_6bar"])
        for index in valid
        if pd.notna(labels.iloc[index].get("max_favorable_excursion_6bar"))
    ]
    mae = [
        abs(float(labels.iloc[index]["max_adverse_excursion_6bar"]))
        for index in valid
        if pd.notna(labels.iloc[index].get("max_adverse_excursion_6bar"))
    ]
    six = returns[6]
    mean_six = sum(six) / len(six) if six else 0.0
    stdev = pd.Series(six).std() if len(six) > 1 else 0.0
    return {
        "count": len(valid),
        **{
            f"mean_forward_return_{horizon}bar": _mean(values)
            for horizon, values in returns.items()
        },
        "median_forward_return_6bar": float(pd.Series(six).median()) if six else 0.0,
        "hit_rate_up_after_cost": sum(1 for value in six if value > cost_threshold) / len(six)
        if six
        else 0.0,
        "mean_mfe": _mean(mfe),
        "mean_mae": _mean(mae),
        "mfe_mae_ratio": _mean(mfe) / _mean(mae) if _mean(mae) else None,
        "information_coefficient_simple": None,
        "t_stat_approx": mean_six / (stdev / math.sqrt(len(six))) if stdev and len(six) else 0.0,
        "cost_adjusted_expected_return": mean_six - cost_threshold,
    }


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
