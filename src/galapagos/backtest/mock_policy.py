from __future__ import annotations

import random
from typing import Any

from galapagos.agent.decision_schema import AgentDecision


def decide_with_policy(
    policy: str,
    context: dict[str, Any],
    *,
    seed: int | None = None,
) -> AgentDecision:
    policy = policy.lower()
    if policy == "always_no_trade":
        return _decision("NO_TRADE", context)
    if policy == "always_long":
        return _entry_decision("LONG", context)
    if policy == "simple_momentum":
        return _simple_momentum(context)
    if policy == "simple_mean_reversion":
        return _simple_mean_reversion(context)
    if policy == "state_aware_momentum":
        return _state_aware_momentum(context)
    if policy == "state_aware_breakout":
        return _state_aware_breakout(context)
    if policy == "state_aware_mean_reversion":
        return _state_aware_mean_reversion(context)
    if policy == "random_with_seed":
        rng = random.Random(seed)
        if rng.random() > 0.5:
            return _entry_decision(rng.choice(["LONG", "SHORT"]), context)
        return _decision("NO_TRADE", context)
    raise ValueError(f"Unsupported mock decision policy: {policy}")


def _simple_momentum(context: dict[str, Any]) -> AgentDecision:
    indicators = context["indicators"]
    regime = indicators.get("market_regime", {})
    if regime.get("volatility_regime") == "extreme":
        return _decision("NO_TRADE", context)
    sma_20 = indicators.get("sma_20")
    sma_50 = indicators.get("sma_50")
    if sma_20 is None or sma_50 is None:
        return _decision("NO_TRADE", context)
    if sma_20 > sma_50:
        return _entry_decision("LONG", context)
    if sma_20 < sma_50:
        return _entry_decision("SHORT", context)
    return _decision("NO_TRADE", context)


def _simple_mean_reversion(context: dict[str, Any]) -> AgentDecision:
    indicators = context["indicators"]
    price = context["market"]["last_close"]
    sma_20 = indicators.get("sma_20")
    if sma_20 is None:
        return _decision("NO_TRADE", context)
    if price < sma_20 * 0.995:
        return _entry_decision("LONG", context, strategy="mean_reversion")
    if price > sma_20 * 1.005:
        return _entry_decision("SHORT", context, strategy="mean_reversion")
    return _decision("NO_TRADE", context)


def _state_aware_momentum(context: dict[str, Any]) -> AgentDecision:
    direction = _momentum_direction(context)
    position = _current_position(context)
    if position:
        if position["side"] == "LONG":
            return _decision("HOLD" if direction == "up" else "CLOSE", context)
        if position["side"] == "SHORT":
            return _decision("HOLD" if direction == "down" else "CLOSE", context)
    if _recently_closed(context):
        return _decision("NO_TRADE", context)
    if direction == "up":
        return _entry_decision("LONG", context, strategy="momentum")
    if direction == "down":
        return _entry_decision("SHORT", context, strategy="momentum")
    return _decision("NO_TRADE", context)


def _state_aware_breakout(context: dict[str, Any]) -> AgentDecision:
    window = _ohlcv_window(context)
    if len(window) < 21:
        return _decision("NO_TRADE", context)
    current = window[-1]
    previous = window[-21:-1]
    close = float(current["close"])
    previous_high = max(float(row["high"]) for row in previous)
    previous_low = min(float(row["low"]) for row in previous)
    margin = 0.001
    breakout_direction = "flat"
    if close > previous_high * (1 + margin):
        breakout_direction = "up"
    elif close < previous_low * (1 - margin):
        breakout_direction = "down"

    position = _current_position(context)
    if position:
        if position["side"] == "LONG":
            if close < previous_high:
                return _decision("CLOSE", context)
            return _decision("HOLD", context)
        if position["side"] == "SHORT":
            if close > previous_low:
                return _decision("CLOSE", context)
            return _decision("HOLD", context)
    if _recently_closed(context):
        return _decision("NO_TRADE", context)
    if breakout_direction == "up":
        return _entry_decision("LONG", context, strategy="breakout")
    if breakout_direction == "down":
        return _entry_decision("SHORT", context, strategy="breakout")
    return _decision("NO_TRADE", context)


def _state_aware_mean_reversion(context: dict[str, Any]) -> AgentDecision:
    window = _ohlcv_window(context)
    if len(window) < 30:
        return _decision("NO_TRADE", context)
    closes = [float(row["close"]) for row in window[-30:]]
    current_price = closes[-1]
    mean = sum(closes) / len(closes)
    variance = sum((price - mean) ** 2 for price in closes) / len(closes)
    std = variance**0.5
    if std <= 0:
        return _decision("NO_TRADE", context)
    z_score = (current_price - mean) / std
    regime = context.get("indicators", {}).get("market_regime", {})
    trend = regime.get("trend")

    position = _current_position(context)
    if position:
        if position["side"] == "LONG":
            if current_price >= mean or z_score > 0:
                return _decision("CLOSE", context)
            return _decision("HOLD", context)
        if position["side"] == "SHORT":
            if current_price <= mean or z_score < 0:
                return _decision("CLOSE", context)
            return _decision("HOLD", context)
    if _recently_closed(context) or trend not in {"range", "unknown"}:
        return _decision("NO_TRADE", context)
    if z_score <= -1.5:
        return _entry_decision("LONG", context, strategy="mean_reversion")
    if z_score >= 1.5:
        return _entry_decision("SHORT", context, strategy="mean_reversion")
    return _decision("NO_TRADE", context)


def _momentum_direction(context: dict[str, Any]) -> str:
    indicators = context["indicators"]
    regime = indicators.get("market_regime", {})
    if regime.get("volatility_regime") == "extreme":
        return "flat"
    sma_20 = indicators.get("sma_20")
    sma_50 = indicators.get("sma_50")
    if sma_20 is None or sma_50 is None or sma_50 == 0:
        return "flat"
    edge = (float(sma_20) - float(sma_50)) / float(sma_50)
    if edge > 0.0005:
        return "up"
    if edge < -0.0005:
        return "down"
    return "flat"


def _current_position(context: dict[str, Any]) -> dict[str, Any] | None:
    portfolio = context.get("portfolio") or {}
    position = portfolio.get("current_position")
    return position if isinstance(position, dict) else None


def _recently_closed(context: dict[str, Any]) -> bool:
    portfolio = context.get("portfolio") or {}
    timestamp = portfolio.get("timestamp")
    recent_trades = context.get("recent_trades") or []
    if not timestamp or not recent_trades:
        return False
    last = recent_trades[-1]
    return last.get("exit_timestamp") == timestamp


def _ohlcv_window(context: dict[str, Any]) -> list[dict[str, Any]]:
    rows = context.get("ohlcv_window") or []
    return [row for row in rows if isinstance(row, dict)]


def _entry_decision(
    side: str,
    context: dict[str, Any],
    strategy: str = "momentum",
) -> AgentDecision:
    profile = context["profile"]
    price = float(context["market"]["last_close"])
    is_long = side == "LONG"
    return AgentDecision(
        decision=side,
        profile=profile["name"],
        asset=profile["symbol"],
        strategy=strategy,
        confidence=0.5,
        reasoning_summary=f"Backtest mock policy generated {side}.",
        horizon=profile["timeframe"],
        reference_entry_price=price,
        stop_loss=price * (0.99 if is_long else 1.01),
        take_profit=price * (1.02 if is_long else 0.98),
        risk_fraction=0.0025,
        max_duration_minutes=profile.get("max_position_duration_minutes", 240),
        invalidation_conditions=[],
        critical_data_used=["price", "volatility"],
    )


def _decision(decision: str, context: dict[str, Any]) -> AgentDecision:
    profile = context["profile"]
    strategy = "no_trade"
    if decision == "CLOSE":
        strategy = "close_position"
    elif decision == "HOLD":
        strategy = "risk_reduction"
    return AgentDecision(
        decision=decision,
        profile=profile["name"],
        asset=profile["symbol"],
        strategy=strategy,
        confidence=0.5,
        reasoning_summary=f"Backtest mock policy generated {decision}.",
        horizon=profile["timeframe"],
        reference_entry_price=None,
        stop_loss=None,
        take_profit=None,
        risk_fraction=0.0,
        max_duration_minutes=0,
        invalidation_conditions=[],
        critical_data_used=[],
    )
