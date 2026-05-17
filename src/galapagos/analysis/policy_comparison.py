from __future__ import annotations

from typing import Any

POLICY_COMPARISON_KEYS = [
    "policy_name",
    "profile",
    "backtest_days",
    "total_trades",
    "trades_per_day",
    "realized_pnl",
    "realized_pnl_per_day",
    "max_drawdown",
    "profit_factor",
    "expectancy",
    "fees_per_day",
    "slippage_per_day",
    "risk_rejected_per_day",
    "no_trade_per_day",
    "exposure_time",
    "average_trade_duration_minutes",
]


def compare_policies(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        policy = str(result.get("policy", "unknown"))
        metrics_by_profile = _metrics_by_profile(result)
        for profile, metrics in metrics_by_profile.items():
            rows.append(
                {
                    "policy_name": policy,
                    "profile": profile,
                    "backtest_days": metrics.get("backtest_days", 0.0),
                    "total_trades": metrics.get("total_trades", 0),
                    "trades_per_day": metrics.get("trades_per_day", 0.0),
                    "realized_pnl": metrics.get("realized_pnl", 0.0),
                    "realized_pnl_per_day": metrics.get("realized_pnl_per_day", 0.0),
                    "max_drawdown": metrics.get("max_drawdown", 0.0),
                    "profit_factor": metrics.get("profit_factor", 0.0),
                    "expectancy": metrics.get("expectancy", 0.0),
                    "fees_per_day": metrics.get("fees_per_day", 0.0),
                    "slippage_per_day": metrics.get("slippage_per_day", 0.0),
                    "risk_rejected_per_day": metrics.get("risk_rejected_per_day", 0.0),
                    "no_trade_per_day": metrics.get("no_trade_per_day", 0.0),
                    "exposure_time": metrics.get("exposure_time", 0.0),
                    "average_trade_duration_minutes": metrics.get(
                        "average_trade_duration_minutes", 0.0
                    ),
                    "win_rate": metrics.get("win_rate", 0.0),
                    "composite_prudent_score": composite_prudent_score(metrics),
                }
            )
    return rows


def _metrics_by_profile(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics = result.get("metrics", {})
    if not metrics:
        return {}
    if all(isinstance(value, dict) for value in metrics.values()):
        return metrics
    profile = str(result.get("profile", "unknown"))
    return {profile: metrics}


def policy_suite_answers(rows: list[dict[str, Any]]) -> dict[str, Any]:
    active = [
        row
        for row in rows
        if row["policy_name"] != "always_no_trade" and row["total_trades"] > 0
    ]
    least_bad = max(active or rows, key=lambda row: row["realized_pnl_per_day"], default=None)
    lowest_reject = min(
        active or rows,
        key=lambda row: (row["risk_rejected_per_day"], -row["realized_pnl_per_day"]),
        default=None,
    )
    state_aware = [row for row in rows if row["policy_name"].startswith("state_aware")]
    simple = [row for row in rows if row["policy_name"] == "simple_momentum"]
    state_reject_avg = _avg(row["risk_rejected_per_day"] for row in state_aware)
    simple_reject_avg = _avg(row["risk_rejected_per_day"] for row in simple)
    thirty = [row for row in rows if row["profile"] == "galapagos_30m"]
    four_h = [row for row in rows if row["profile"] == "galapagos_4h"]
    return {
        "least_losing_policy": least_bad,
        "lowest_risk_reject_policy": lowest_reject,
        "recommended_llm_reference_baseline": least_bad,
        "state_aware_reduces_rejects": state_reject_avg < simple_reject_avg,
        "state_aware_risk_reject_per_day_avg": state_reject_avg,
        "simple_momentum_risk_reject_per_day_avg": simple_reject_avg,
        "thirty_m_avg_fees_per_day": _avg(row["fees_per_day"] for row in thirty),
        "four_h_avg_fees_per_day": _avg(row["fees_per_day"] for row in four_h),
        "thirty_m_avg_drawdown": _avg(row["max_drawdown"] for row in thirty),
        "four_h_avg_drawdown": _avg(row["max_drawdown"] for row in four_h),
        "rankings": rank_policies(rows),
    }


def composite_prudent_score(metrics: dict[str, Any]) -> float:
    return (
        float(metrics.get("realized_pnl_per_day") or 0.0)
        - abs(float(metrics.get("max_drawdown") or 0.0)) * 100
        - float(metrics.get("fees_per_day") or 0.0) * 0.1
        - float(metrics.get("slippage_per_day") or 0.0) * 0.1
        - float(metrics.get("risk_rejected_per_day") or 0.0) * 2
    )


def rank_policies(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return {
        "best_pnl_per_day": max(rows, key=lambda row: row["realized_pnl_per_day"]),
        "lowest_drawdown": max(rows, key=lambda row: row["max_drawdown"]),
        "lowest_slippage_per_day": min(rows, key=lambda row: row["slippage_per_day"]),
        "lowest_risk_rejects": min(rows, key=lambda row: row["risk_rejected_per_day"]),
        "best_expectancy": max(rows, key=lambda row: row["expectancy"]),
        "best_composite_prudent_score": max(
            rows, key=lambda row: row["composite_prudent_score"]
        ),
    }


def _avg(values) -> float:
    materialized = [float(value) for value in values]
    if not materialized:
        return 0.0
    return sum(materialized) / len(materialized)
