from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from galapagos.agent.decision_validator import unavailable_derivative_features


@dataclass(frozen=True)
class DecisionContext:
    metadata: dict[str, Any]
    market: dict[str, Any]
    derivatives: dict[str, Any]
    portfolio: dict[str, Any]
    risk_constraints: dict[str, Any]
    costs: dict[str, Any]
    candidate_scenarios: list[dict[str, Any]]
    candidate_setup: dict[str, Any]
    available_critical_data: dict[str, bool]
    unavailable_features: list[str]
    context_hash: str = field(default="")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["context_hash"] = self.context_hash or _stable_hash(
            {key: value for key, value in payload.items() if key != "context_hash"}
        )
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, default=str)


def build_decision_context(
    *,
    profile: dict[str, Any],
    market: dict[str, Any],
    indicators: dict[str, Any],
    derivatives: dict[str, Any],
    scenarios: list[dict[str, Any]],
    portfolio: dict[str, Any],
    risk_config: dict[str, Any],
    decision_timestamp: str,
    data_mode: str,
    run_id: str,
    experiment_id: str | None = None,
    ohlcv_window: list[dict[str, Any]] | None = None,
    recent_decisions: list[dict[str, Any]] | None = None,
    recent_trades: list[dict[str, Any]] | None = None,
    candidate_setup: dict[str, Any] | None = None,
) -> DecisionContext:
    unavailable = sorted(unavailable_derivative_features(derivatives))
    recent_decisions = recent_decisions or []
    recent_trades = recent_trades or []
    ohlcv_window = ohlcv_window or []
    market_payload = _market_payload(market, indicators, ohlcv_window)
    portfolio_payload = _portfolio_payload(portfolio, recent_decisions, recent_trades)
    derivatives_payload = _derivatives_payload(derivatives, unavailable)
    candidate_scenarios = _candidate_scenarios(scenarios, market_payload["current_price"])
    candidate_payload = _candidate_setup_payload(candidate_setup)
    costs_payload = _cost_awareness_payload(candidate_payload)
    payload = {
        "metadata": {
            "profile": profile["name"],
            "asset": profile["symbol"],
            "timeframe": profile["timeframe"],
            "decision_timestamp": decision_timestamp,
            "data_mode": data_mode,
            "run_id": run_id,
            "experiment_id": experiment_id,
        },
        "market": market_payload,
        "derivatives": derivatives_payload,
        "portfolio": portfolio_payload,
        "risk_constraints": {
            "max_risk_per_trade": risk_config.get("max_risk_per_trade"),
            "max_open_positions_per_profile": risk_config.get(
                "max_open_positions_per_profile"
            ),
            "max_daily_loss": risk_config.get("max_daily_loss"),
            "stop_loss_required": risk_config.get("stop_loss_required", True),
            "take_profit_or_time_exit_required": risk_config.get(
                "take_profit_or_time_exit_required", True
            ),
            "leverage_allowed": risk_config.get("leverage_allowed", False),
            "paper_trading_only": profile.get("paper_trading_only", True),
        },
        "costs": costs_payload,
        "candidate_scenarios": candidate_scenarios,
        "candidate_setup": candidate_payload,
        "available_critical_data": _available_critical_data(
            market_payload,
            derivatives_payload,
            candidate_setup,
        ),
        "unavailable_features": unavailable,
    }
    return DecisionContext(**payload, context_hash=_stable_hash(payload))


def _market_payload(
    market: dict[str, Any],
    indicators: dict[str, Any],
    ohlcv_window: list[dict[str, Any]],
) -> dict[str, Any]:
    current_price = float(market.get("last_close") or market.get("current_price") or 0.0)
    closes = [float(row.get("close")) for row in ohlcv_window if row.get("close") is not None]
    recent_return = 0.0
    if len(closes) >= 2 and closes[-2]:
        recent_return = (closes[-1] - closes[-2]) / closes[-2]
    highs = [float(row.get("high")) for row in ohlcv_window[-50:] if row.get("high") is not None]
    lows = [float(row.get("low")) for row in ohlcv_window[-50:] if row.get("low") is not None]
    return {
        "current_price": current_price,
        "recent_ohlcv_summary": {
            "bars": len(ohlcv_window),
            "last_open": market.get("last_open"),
            "last_high": market.get("last_high"),
            "last_low": market.get("last_low"),
            "last_close": current_price,
            "last_volume": market.get("last_volume"),
        },
        "recent_return": recent_return,
        "volatility": indicators.get("realized_volatility"),
        "trend_short": _trend_from_sma(indicators.get("sma_20"), current_price),
        "trend_long": _trend_from_sma(indicators.get("sma_50"), current_price),
        "support_resistance": {
            "support": min(lows) if lows else None,
            "resistance": max(highs) if highs else None,
        },
        "market_regime": indicators.get("market_regime", {}),
    }


def _portfolio_payload(
    portfolio: dict[str, Any],
    recent_decisions: list[dict[str, Any]],
    recent_trades: list[dict[str, Any]],
) -> dict[str, Any]:
    position = portfolio.get("current_position")
    current_price = float(portfolio.get("current_price") or 0.0)
    entry_price = float(position.get("entry_price") or 0.0) if position else None
    unrealized = float(portfolio.get("unrealized_pnl") or 0.0)
    side = position.get("side") if position else None
    if position and entry_price and current_price:
        direction = 1 if side == "LONG" else -1
        unrealized_percent = (current_price - entry_price) / entry_price * direction
    else:
        unrealized_percent = 0.0
    return {
        "has_open_position": bool(position),
        "position_side": side,
        "entry_price": entry_price,
        "unrealized_pnl": unrealized,
        "unrealized_pnl_percent": unrealized_percent,
        "bars_in_position": portfolio.get("bars_in_position", 0),
        "max_duration_remaining": _max_duration_remaining(position, portfolio),
        "current_stop_loss": position.get("stop_loss") if position else None,
        "current_take_profit": position.get("take_profit") if position else None,
        "trades_today": len(recent_trades),
        "risk_rejections_recent": sum(
            1 for decision in recent_decisions if not decision.get("risk_approved", True)
        ),
        "last_decision": recent_decisions[-1] if recent_decisions else None,
        "last_trade_result": recent_trades[-1] if recent_trades else None,
    }


def _max_duration_remaining(
    position: dict[str, Any] | None,
    portfolio: dict[str, Any],
) -> int | None:
    if not position:
        return None
    max_duration = int(position.get("max_duration_minutes") or 0)
    bars = int(portfolio.get("bars_in_position") or 0)
    return max(0, max_duration - bars)


def _derivatives_payload(derivatives: dict[str, Any], unavailable: list[str]) -> dict[str, Any]:
    keys = [
        "funding",
        "funding_previous",
        "open_interest",
        "open_interest_change",
        "long_short_ratio",
        "basis",
        "liquidations",
    ]
    payload = {key: derivatives.get(key) for key in keys}
    payload["derivatives_availability_summary"] = {
        key: (
            (value or {}).get("status", "unavailable")
            if isinstance(value, dict)
            else "unavailable"
        )
        for key, value in payload.items()
        if key in keys
    }
    payload["unavailable_features"] = unavailable
    return payload


def _candidate_scenarios(
    scenarios: list[dict[str, Any]],
    current_price: float,
) -> list[dict[str, Any]]:
    output = []
    for scenario in scenarios:
        side = scenario.get("side") or scenario.get("direction")
        strategy = scenario.get("strategy") or scenario.get("name") or "unknown"
        output.append(
            {
                "strategy": strategy,
                "side": side,
                "confidence_hint": scenario.get("confidence") or scenario.get("confidence_hint"),
                "invalidation": scenario.get("invalidation") or scenario.get("reason"),
                "suggested_stop": scenario.get("suggested_stop")
                or _suggested_stop(side, current_price),
                "suggested_take_profit": scenario.get("suggested_take_profit")
                or _suggested_take_profit(side, current_price),
                "reason_summary": scenario.get("reason_summary") or scenario.get("reason"),
            }
        )
    return output


def _candidate_setup_payload(candidate_setup: dict[str, Any] | None) -> dict[str, Any]:
    if not candidate_setup:
        return {
            "exists": False,
            "source_policy": None,
            "proposed_decision": None,
            "proposed_strategy": None,
            "proposed_entry": None,
            "proposed_stop_loss": None,
            "proposed_take_profit": None,
            "reason_summary": None,
            "quality_hint": None,
            "instruction": "No baseline candidate setup is supplied.",
        }
    return {
        "exists": True,
        "source_policy": candidate_setup.get("baseline_policy")
        or candidate_setup.get("source_policy"),
        "proposed_decision": candidate_setup.get("baseline_decision")
        or candidate_setup.get("proposed_decision"),
        "proposed_strategy": candidate_setup.get("baseline_strategy")
        or candidate_setup.get("proposed_strategy"),
        "proposed_entry": candidate_setup.get("current_price")
        or candidate_setup.get("proposed_entry"),
        "proposed_stop_loss": candidate_setup.get("suggested_stop_loss")
        or candidate_setup.get("proposed_stop_loss"),
        "proposed_take_profit": candidate_setup.get("suggested_take_profit")
        or candidate_setup.get("proposed_take_profit"),
        "reason_summary": candidate_setup.get("baseline_reason_summary")
        or candidate_setup.get("reason_summary"),
        "quality_hint": candidate_setup.get("quality_hint") or "candidate_from_baseline",
        "instruction": (
            "A mechanical baseline proposes this setup, but you must validate or refuse it. "
            "You are not required to follow the baseline. If the setup is insufficient, "
            "respond NO_TRADE."
        ),
    }


def _cost_awareness_payload(candidate_setup: dict[str, Any]) -> dict[str, Any]:
    fee_rate = 0.001
    slippage_bps = 5.0
    round_trip_cost_fraction = (2 * fee_rate) + (2 * slippage_bps / 10_000)
    entry = candidate_setup.get("proposed_entry")
    take_profit = candidate_setup.get("proposed_take_profit")
    candidate_expected_move = None
    if entry and take_profit:
        candidate_expected_move = abs(float(take_profit) - float(entry)) / float(entry)
    return {
        "estimated_fee_rate": fee_rate,
        "estimated_slippage_bps": slippage_bps,
        "estimated_round_trip_cost": round_trip_cost_fraction,
        "minimum_expected_move_to_break_even": round_trip_cost_fraction,
        "candidate_expected_move": candidate_expected_move,
        "instruction": (
            "Consider round-trip fees and slippage before validating a candidate setup. "
            "A setup with expected move close to cost has weak edge."
        ),
    }


def _available_critical_data(
    market_payload: dict[str, Any],
    derivatives_payload: dict[str, Any],
    candidate_setup: dict[str, Any] | None,
) -> dict[str, bool]:
    availability = derivatives_payload.get("derivatives_availability_summary", {})
    return {
        "price": bool(market_payload.get("current_price")),
        "volatility": market_payload.get("volatility") is not None,
        "trend_short": bool(market_payload.get("trend_short")),
        "trend_long": bool(market_payload.get("trend_long")),
        "market_regime": bool(market_payload.get("market_regime")),
        "candidate_setup": bool(candidate_setup),
        "funding": availability.get("funding") == "available",
        "open_interest": availability.get("open_interest") == "available",
    }


def _trend_from_sma(sma: float | None, current_price: float) -> str:
    if sma is None or current_price <= 0:
        return "unknown"
    if current_price > sma:
        return "up"
    if current_price < sma:
        return "down"
    return "flat"


def _suggested_stop(side: str | None, price: float) -> float | None:
    if not side or price <= 0:
        return None
    return price * (0.99 if side == "LONG" else 1.01)


def _suggested_take_profit(side: str | None, price: float) -> float | None:
    if not side or price <= 0:
        return None
    return price * (1.02 if side == "LONG" else 0.98)


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
