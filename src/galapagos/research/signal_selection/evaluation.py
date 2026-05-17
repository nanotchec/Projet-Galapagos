"""Evaluate selected signal subsets."""
from __future__ import annotations

from typing import Any

import pandas as pd


def evaluate_rule_subset(
    all_policy_frame: pd.DataFrame,
    selected: pd.DataFrame,
    *,
    rule_name: str,
    policy: str,
    random_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    total = len(all_policy_frame)
    selected_count = len(selected)
    stats = _basic_stats(selected)
    all_stats = _basic_stats(all_policy_frame)
    random_stats = random_stats or {}
    improvement = stats["net_mean_pnl_pct"] - all_stats["net_mean_pnl_pct"]
    verdict = _verdict(selected_count, stats, random_stats)
    return {
        "policy": policy,
        "rule_name": rule_name,
        "selected_count": selected_count,
        "selection_ratio": float(selected_count / total) if total else 0.0,
        **stats,
        "improvement_vs_all_candidates": float(improvement),
        "random_same_count_mean": random_stats.get("random_mean"),
        "random_same_count_p05": random_stats.get("random_p05"),
        "random_same_count_p95": random_stats.get("random_p95"),
        "beats_random_mean": bool(
            stats["net_mean_pnl_pct"] > random_stats.get("random_mean", float("inf"))
        )
        if selected_count
        else False,
        "beats_random_p95": bool(
            stats["net_mean_pnl_pct"] > random_stats.get("random_p95", float("inf"))
        )
        if selected_count
        else False,
        "enough_sample_size": selected_count >= 30,
        "verdict": verdict,
    }


def _basic_stats(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {
            "gross_mean_pnl_pct": 0.0,
            "net_mean_pnl_pct": 0.0,
            "net_median_pnl_pct": 0.0,
            "total_net_pnl_pct": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "average_cost_pct": 0.0,
            "cost_flip_count": 0,
            "max_drawdown": 0.0,
            "trades_per_month": 0.0,
        }
    gross = pd.to_numeric(frame["gross_pnl_pct"], errors="coerce").fillna(0.0)
    net = pd.to_numeric(frame["net_pnl_pct"], errors="coerce").fillna(0.0)
    costs = pd.to_numeric(frame["cost_pct"], errors="coerce").fillna(0.0)
    wins = net[net > 0].sum()
    losses = net[net < 0].abs().sum()
    return {
        "gross_mean_pnl_pct": float(gross.mean()),
        "net_mean_pnl_pct": float(net.mean()),
        "net_median_pnl_pct": float(net.median()),
        "total_net_pnl_pct": float(net.sum()),
        "win_rate": float((net > 0).mean()),
        "profit_factor": float(wins / losses) if losses > 0 else float("inf") if wins > 0 else 0.0,
        "average_cost_pct": float(costs.mean()),
        "cost_flip_count": int(((gross > 0) & (net <= 0)).sum()),
        "max_drawdown": _max_drawdown(net),
        "trades_per_month": _trades_per_month(frame),
    }


def _max_drawdown(net_returns: pd.Series) -> float:
    curve = net_returns.cumsum()
    drawdown = curve - curve.cummax()
    return float(drawdown.min()) if len(drawdown) else 0.0


def _trades_per_month(frame: pd.DataFrame) -> float:
    ts = pd.to_datetime(frame["timestamp"], utc=True)
    if ts.empty:
        return 0.0
    days = max((ts.max() - ts.min()).total_seconds() / 86400, 1.0)
    return float(len(frame) / (days / 30.4375))


def _verdict(
    selected_count: int,
    stats: dict[str, Any],
    random_stats: dict[str, Any],
) -> list[str]:
    verdicts: list[str] = []
    if selected_count == 0:
        return ["NO_TRADE_BASELINE"]
    if selected_count < 30:
        verdicts.append("SAMPLE_TOO_SMALL")
    if stats["net_mean_pnl_pct"] <= 0:
        verdicts.append("FILTER_FAILS_AFTER_COSTS")
    else:
        verdicts.append("PROMISING_BUT_UNVALIDATED")
    random_p95 = random_stats.get("random_p95")
    random_mean = random_stats.get("random_mean")
    if random_p95 is not None and stats["net_mean_pnl_pct"] > random_p95:
        verdicts.append("BEATS_RANDOM_P95_PROMISING_BUT_UNVALIDATED")
    elif random_p95 is not None:
        verdicts.append("NOT_DISTINGUISHABLE_FROM_RANDOM")
    elif random_mean is not None and stats["net_mean_pnl_pct"] > random_mean:
        verdicts.append("BEATS_RANDOM_MEAN_ONLY")
    return verdicts
