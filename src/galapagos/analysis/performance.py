from __future__ import annotations

import json
from typing import Any


def summarize_trades(trades: list[dict]) -> dict:
    pnl = sum(float(trade.get("pnl") or 0.0) for trade in trades)
    wins = sum(1 for trade in trades if float(trade.get("pnl") or 0.0) > 0)
    return {
        "trade_count": len(trades),
        "total_pnl": pnl,
        "win_rate": wins / len(trades) if trades else 0.0,
    }


def summarize_profile_performance(
    *,
    profile: str,
    trades: list[dict[str, Any]],
    open_positions: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    current_price: float | None = None,
) -> dict[str, Any]:
    closed_trades = [trade for trade in trades if trade.get("status") == "CLOSED"]
    realized_pnl = sum(float(trade.get("pnl") or 0.0) for trade in closed_trades)
    wins = sum(1 for trade in closed_trades if float(trade.get("pnl") or 0.0) > 0)
    unrealized_pnl = sum(_unrealized(position, current_price) for position in open_positions)
    no_trade_count = 0
    risk_rejected_count = 0
    for decision in decisions:
        parsed = _loads(decision.get("parsed_decision"))
        risk = _loads(decision.get("risk_engine_result"))
        if parsed.get("decision") == "NO_TRADE":
            no_trade_count += 1
        if risk and not risk.get("approved", True):
            risk_rejected_count += 1
    return {
        "profile": profile,
        "trade_count": len(trades),
        "closed_trade_count": len(closed_trades),
        "open_position_count": len(open_positions),
        "realized_pnl": realized_pnl,
        "unrealized_pnl": unrealized_pnl,
        "total_pnl": realized_pnl,
        "total_fees": sum(float(trade.get("fees") or 0.0) for trade in closed_trades),
        "total_slippage": sum(float(trade.get("slippage") or 0.0) for trade in closed_trades),
        "win_rate": wins / len(closed_trades) if closed_trades else 0.0,
        "risk_rejected_count": risk_rejected_count,
        "no_trade_count": no_trade_count,
    }


def _unrealized(position: dict[str, Any], current_price: float | None) -> float:
    if current_price is None:
        return 0.0
    entry = float(position.get("entry_price") or 0.0)
    size = float(position.get("size") or 0.0)
    if position.get("side") == "LONG":
        return (current_price - entry) * size
    return (entry - current_price) * size


def _loads(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
