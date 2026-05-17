"""Metrics calculation for trade simulation results."""
from __future__ import annotations

from typing import Any

import pandas as pd

from .schema import TradeSimulationResult


def calculate_policy_metrics(results: list[TradeSimulationResult]) -> dict[str, Any]:
    """Calculate summary metrics for a set of simulation results."""
    if not results:
        return {
            "candidates_count": 0,
            "evaluated_count": 0,
            "win_rate": 0.0,
            "mean_pnl_pct": 0.0,
            "mean_pnl_after_cost_pct": 0.0,
        }

    df = pd.DataFrame([r.model_dump() for r in results])

    total = len(df)
    evaluated = df[df["simulation_status"] == "complete"]
    eval_count = len(evaluated)

    if eval_count == 0:
        return {
            "candidates_count": total,
            "evaluated_count": 0,
            "win_rate": 0.0,
            "mean_pnl_pct": 0.0,
            "mean_pnl_after_cost_pct": 0.0,
        }

    # Basic performance
    win_rate = (evaluated["pnl_pct"] > 0).mean()
    mean_pnl = evaluated["pnl_pct"].mean()
    mean_pnl_after_cost = evaluated["pnl_after_cost_pct"].mean()
    median_pnl_after_cost = evaluated["pnl_after_cost_pct"].median()

    # Risk metrics
    mean_mfe = evaluated["mfe_pct"].mean()
    mean_mae = evaluated["mae_pct"].mean()

    # Exits
    exit_reasons = evaluated["exit_reason"].value_counts().to_dict()

    # Recent window check (2026)
    df["dt"] = pd.to_datetime(df["signal_time"])
    recent = df[df["dt"].dt.year >= 2026]
    recent_eval = recent[recent["simulation_status"] == "complete"]
    recent_count = len(recent_eval)
    recent_win_rate = (recent_eval["pnl_pct"] > 0).mean() if recent_count > 0 else 0.0
    recent_pnl_after_cost = (
        recent_eval["pnl_after_cost_pct"].mean() if recent_count > 0 else 0.0
    )

    evaluated_ratio = eval_count / total if total > 0 else 0.0

    return {
        "candidates_count": total,
        "evaluated_count": eval_count,
        "missing_intrabar_count": total - eval_count,
        "evaluated_ratio": float(evaluated_ratio),
        "intrabar_sample_limited": evaluated_ratio < 0.2,
        "win_rate": float(win_rate),
        "mean_pnl_pct": float(mean_pnl),
        "mean_pnl_after_cost_pct": float(mean_pnl_after_cost),
        "median_pnl_after_cost_pct": float(median_pnl_after_cost),
        "mean_mfe_pct": float(mean_mfe),
        "mean_mae_pct": float(mean_mae),
        "exit_reasons": {str(k): int(v) for k, v in exit_reasons.items()},
        "ambiguous_rate": float(evaluated["ambiguous"].mean()),
        "recent_window": {
            "count": recent_count,
            "win_rate": float(recent_win_rate),
            "mean_pnl_after_cost_pct": float(recent_pnl_after_cost),
        },
    }
