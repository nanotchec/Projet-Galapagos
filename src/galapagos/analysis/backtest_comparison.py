from __future__ import annotations

from typing import Any

BACKTEST_METRIC_KEYS = [
    "total_trades",
    "closed_trades",
    "realized_pnl",
    "unrealized_pnl",
    "total_fees",
    "total_slippage",
    "max_drawdown",
    "profit_factor",
    "expectancy",
    "average_win",
    "average_loss",
    "average_trade_duration_minutes",
    "exposure_time",
    "exposure_time_percent",
    "backtest_days",
    "realized_pnl_per_day",
    "fees_per_day",
    "slippage_per_day",
    "trades_per_day",
    "risk_rejected_per_day",
    "no_trade_per_day",
    "no_trade_count",
    "risk_rejected_count",
]


def compare_backtest_profiles(profile_metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    profiles = {
        profile: {key: metrics.get(key, 0.0) for key in BACKTEST_METRIC_KEYS}
        for profile, metrics in profile_metrics.items()
    }
    result: dict[str, Any] = {"profiles": profiles}
    if len(profiles) > 1:
        days = {
            profile: _num(metrics.get("backtest_days"))
            for profile, metrics in profiles.items()
        }
        result["period_equivalence"] = {
            "backtest_days_by_profile": days,
            "equivalent": _periods_equivalent(days),
        }
    thirty = profiles.get("galapagos_30m")
    four_h = profiles.get("galapagos_4h")
    if thirty is not None and four_h is not None:
        result["deltas"] = {
            "realized_pnl_delta_30m_minus_4h": _num(thirty["realized_pnl"])
            - _num(four_h["realized_pnl"]),
            "total_trades_delta_30m_minus_4h": _num(thirty["total_trades"])
            - _num(four_h["total_trades"]),
            "max_drawdown_delta_30m_minus_4h": _num(thirty["max_drawdown"])
            - _num(four_h["max_drawdown"]),
            "expectancy_delta_30m_minus_4h": _num(thirty["expectancy"])
            - _num(four_h["expectancy"]),
            "exposure_time_delta_30m_minus_4h": _num(thirty["exposure_time"])
            - _num(four_h["exposure_time"]),
            "realized_pnl_per_day_delta_30m_minus_4h": _num(thirty["realized_pnl_per_day"])
            - _num(four_h["realized_pnl_per_day"]),
            "trades_per_day_delta_30m_minus_4h": _num(thirty["trades_per_day"])
            - _num(four_h["trades_per_day"]),
            "fees_per_day_delta_30m_minus_4h": _num(thirty["fees_per_day"])
            - _num(four_h["fees_per_day"]),
            "slippage_per_day_delta_30m_minus_4h": _num(thirty["slippage_per_day"])
            - _num(four_h["slippage_per_day"]),
            "risk_rejected_per_day_delta_30m_minus_4h": _num(
                thirty["risk_rejected_per_day"]
            )
            - _num(four_h["risk_rejected_per_day"]),
        }
    return result


def _num(value: Any) -> float:
    if value == float("inf"):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _periods_equivalent(days: dict[str, float]) -> bool:
    values = [value for value in days.values() if value > 0]
    if len(values) < 2:
        return True
    return max(values) - min(values) <= 0.25
