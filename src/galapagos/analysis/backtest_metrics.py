from __future__ import annotations

from datetime import datetime
from typing import Any


def calculate_backtest_metrics(
    *,
    trades: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    equity_curve: list[dict[str, Any]],
    total_bars: int,
    open_positions: list[dict[str, Any]],
    current_price: float | None,
    backtest_days: float | None = None,
) -> dict[str, Any]:
    closed = [trade for trade in trades if trade.get("status") == "CLOSED"]
    pnls = [float(trade.get("pnl") or 0.0) for trade in closed]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    realized = sum(pnls)
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    no_trade_count = sum(1 for decision in decisions if decision.get("decision") == "NO_TRADE")
    risk_rejected_count = sum(
        1 for decision in decisions if not decision.get("risk_approved", True)
    )
    total_fees = sum(float(trade.get("fees") or 0.0) for trade in closed)
    total_slippage = sum(float(trade.get("slippage") or 0.0) for trade in closed)
    exposure_time = _exposure_time(equity_curve)
    days = _backtest_days(equity_curve, backtest_days)
    return {
        "total_trades": len(trades),
        "closed_trades": len(closed),
        "win_rate": len(wins) / len(closed) if closed else 0.0,
        "realized_pnl": realized,
        "unrealized_pnl": _unrealized(open_positions, current_price),
        "total_fees": total_fees,
        "total_slippage": total_slippage,
        "max_drawdown": _max_drawdown(equity_curve),
        "profit_factor": (
            gross_win / gross_loss if gross_loss else (float("inf") if gross_win else 0.0)
        ),
        "expectancy": realized / len(closed) if closed else 0.0,
        "average_win": sum(wins) / len(wins) if wins else 0.0,
        "average_loss": sum(losses) / len(losses) if losses else 0.0,
        "average_trade_duration_minutes": _average_trade_duration_minutes(closed),
        "exposure_time": exposure_time,
        "exposure_time_percent": exposure_time * 100,
        "backtest_days": days,
        "realized_pnl_per_day": _per_day(realized, days),
        "fees_per_day": _per_day(total_fees, days),
        "slippage_per_day": _per_day(total_slippage, days),
        "trades_per_day": _per_day(len(trades), days),
        "risk_rejected_per_day": _per_day(risk_rejected_count, days),
        "no_trade_per_day": _per_day(no_trade_count, days),
        "no_trade_count": no_trade_count,
        "risk_rejected_count": risk_rejected_count,
    }


def _max_drawdown(equity_curve: list[dict[str, Any]]) -> float:
    peak: float | None = None
    drawdown = 0.0
    for point in equity_curve:
        equity = float(point.get("equity") or 0.0)
        peak = equity if peak is None else max(peak, equity)
        if peak:
            drawdown = min(drawdown, (equity - peak) / peak)
    return drawdown


def _exposure_time(equity_curve: list[dict[str, Any]]) -> float:
    if not equity_curve:
        return 0.0
    exposed = sum(1 for point in equity_curve if point.get("open_position_count", 0) > 0)
    return max(0.0, min(1.0, exposed / len(equity_curve)))


def _backtest_days(equity_curve: list[dict[str, Any]], explicit_days: float | None) -> float:
    if explicit_days is not None and explicit_days > 0:
        return explicit_days
    if len(equity_curve) < 2:
        return 0.0
    start = _parse_timestamp(equity_curve[0].get("timestamp"))
    end = _parse_timestamp(equity_curve[-1].get("timestamp"))
    if start is None or end is None or end <= start:
        return 0.0
    return (end - start).total_seconds() / 86_400


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _per_day(value: float, days: float) -> float:
    if days <= 0:
        return 0.0
    return float(value) / days


def _average_trade_duration_minutes(trades: list[dict[str, Any]]) -> float:
    durations: list[float] = []
    for trade in trades:
        entry = _parse_timestamp(trade.get("entry_timestamp"))
        exit_ = _parse_timestamp(trade.get("exit_timestamp"))
        if entry is None or exit_ is None or exit_ < entry:
            continue
        durations.append((exit_ - entry).total_seconds() / 60)
    if not durations:
        return 0.0
    return sum(durations) / len(durations)


def _unrealized(open_positions: list[dict[str, Any]], current_price: float | None) -> float:
    if current_price is None:
        return 0.0
    total = 0.0
    for position in open_positions:
        entry = float(position.get("entry_price") or 0.0)
        size = float(position.get("size") or 0.0)
        if position.get("side") == "LONG":
            total += (current_price - entry) * size
        else:
            total += (entry - current_price) * size
    return total
