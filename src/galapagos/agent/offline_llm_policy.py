from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from galapagos.agent.decision_context import DecisionContext


@dataclass(frozen=True)
class OfflineLLMResponse:
    policy_name: str
    raw_response: str


OFFLINE_LLM_POLICIES = {
    "llm_offline_conservative",
    "llm_offline_balanced",
    "llm_offline_aggressive",
}


def is_offline_llm_policy(policy_name: str) -> bool:
    return policy_name in OFFLINE_LLM_POLICIES


def generate_offline_llm_response(
    policy_name: str,
    context: DecisionContext,
) -> OfflineLLMResponse:
    payload = context.to_dict()
    if policy_name == "llm_offline_conservative":
        decision = _decide(payload, min_strength=0.012, risk_fraction=0.001, avoid_30m=True)
    elif policy_name == "llm_offline_balanced":
        decision = _decide(payload, min_strength=0.004, risk_fraction=0.0025, avoid_30m=False)
    elif policy_name == "llm_offline_aggressive":
        decision = _decide(payload, min_strength=0.001, risk_fraction=0.004, avoid_30m=False)
    else:
        raise ValueError(f"Unsupported offline LLM policy: {policy_name}")
    return OfflineLLMResponse(policy_name=policy_name, raw_response=json.dumps(decision))


def _decide(
    context: dict[str, Any],
    *,
    min_strength: float,
    risk_fraction: float,
    avoid_30m: bool,
) -> dict[str, Any]:
    metadata = context["metadata"]
    market = context["market"]
    portfolio = context["portfolio"]
    price = float(market["current_price"])
    direction, strength = _direction_and_strength(market, context["candidate_scenarios"])
    if portfolio["has_open_position"]:
        side = portfolio["position_side"]
        if side == "LONG":
            return _base_decision("HOLD" if direction == "up" else "CLOSE", context)
        if side == "SHORT":
            return _base_decision("HOLD" if direction == "down" else "CLOSE", context)
        return _base_decision("NO_TRADE", context)
    if avoid_30m and metadata["timeframe"] == "30m" and strength < min_strength * 2:
        return _base_decision("NO_TRADE", context)
    if strength < min_strength or direction == "flat":
        return _base_decision("NO_TRADE", context)
    side = "LONG" if direction == "up" else "SHORT"
    return _entry(side, context, price=price, risk_fraction=risk_fraction, strength=strength)


def _direction_and_strength(
    market: dict[str, Any],
    scenarios: list[dict[str, Any]],
) -> tuple[str, float]:
    trend_short = market.get("trend_short")
    trend_long = market.get("trend_long")
    recent_return = float(market.get("recent_return") or 0.0)
    if trend_short == "up" and trend_long == "up":
        direction = "up"
    elif trend_short == "down" and trend_long == "down":
        direction = "down"
    elif recent_return > 0:
        direction = "up"
    elif recent_return < 0:
        direction = "down"
    else:
        direction = "flat"
    scenario_bonus = 0.0
    for scenario in scenarios:
        if scenario.get("side") == ("LONG" if direction == "up" else "SHORT"):
            scenario_bonus = max(scenario_bonus, float(scenario.get("confidence_hint") or 0.0))
    strength = abs(recent_return) + scenario_bonus * 0.01
    return direction, strength


def _entry(
    side: str,
    context: dict[str, Any],
    *,
    price: float,
    risk_fraction: float,
    strength: float,
) -> dict[str, Any]:
    is_long = side == "LONG"
    return {
        **_identity(side, context),
        "strategy": "momentum" if strength < 0.02 else "breakout",
        "confidence": min(0.85, 0.5 + strength),
        "reasoning_summary": f"Offline LLM simulated {side} from aligned context.",
        "reference_entry_price": price,
        "stop_loss": price * (0.992 if is_long else 1.008),
        "take_profit": price * (1.016 if is_long else 0.984),
        "risk_fraction": risk_fraction,
        "max_duration_minutes": _max_duration(context),
        "invalidation_conditions": ["Momentum direction flips", "Risk constraints fail"],
        "critical_data_used": ["price", "volatility"],
    }


def _base_decision(decision: str, context: dict[str, Any]) -> dict[str, Any]:
    strategy = "no_trade"
    if decision == "HOLD":
        strategy = "risk_reduction"
    elif decision == "CLOSE":
        strategy = "close_position"
    return {
        **_identity(decision, context),
        "strategy": strategy,
        "confidence": 0.55,
        "reasoning_summary": f"Offline LLM simulated {decision}.",
        "reference_entry_price": None,
        "stop_loss": None,
        "take_profit": None,
        "risk_fraction": 0.0,
        "max_duration_minutes": 0,
        "invalidation_conditions": [],
        "critical_data_used": [],
    }


def _identity(decision: str, context: dict[str, Any]) -> dict[str, Any]:
    metadata = context["metadata"]
    return {
        "decision": decision,
        "profile": metadata["profile"],
        "asset": metadata["asset"],
        "horizon": metadata["timeframe"],
    }


def _max_duration(context: dict[str, Any]) -> int:
    timeframe = context["metadata"]["timeframe"]
    return 240 if timeframe == "30m" else 1440
