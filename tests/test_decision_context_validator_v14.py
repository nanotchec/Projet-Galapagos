from galapagos.agent.decision_schema import AgentDecision
from galapagos.agent.decision_validator import validate_decision_context


def base_decision(**overrides) -> AgentDecision:
    payload = {
        "decision": "LONG",
        "profile": "galapagos_30m",
        "asset": "BTC/USD",
        "strategy": "breakout",
        "confidence": 0.6,
        "reasoning_summary": "Valid.",
        "horizon": "30m",
        "reference_entry_price": 100.0,
        "stop_loss": 99.0,
        "take_profit": 102.0,
        "risk_fraction": 0.002,
        "max_duration_minutes": 240,
        "invalidation_conditions": [],
        "critical_data_used": ["price", "volatility"],
    }
    payload.update(overrides)
    return AgentDecision(**payload)


def context_config() -> dict:
    return {
        "context_validation": {
            "enabled": True,
            "max_entry_price_deviation_bps": 50,
            "unavailable_data_policy": "fallback_no_trade",
        }
    }


def profile() -> dict:
    return {"name": "galapagos_30m", "symbol": "BTC/USD", "timeframe": "30m"}


def derivatives() -> dict:
    return {"funding": {"status": "unavailable"}, "open_interest": {"status": "available"}}


def test_wrong_profile_falls_back_to_no_trade() -> None:
    result = validate_decision_context(
        base_decision(profile="galapagos_4h"),
        profile=profile(),
        market={"last_close": 100},
        derivatives=derivatives(),
        config=context_config(),
    )
    assert result.validity == "context_fallback"
    assert result.decision.decision == "NO_TRADE"


def test_wrong_asset_falls_back_to_no_trade() -> None:
    result = validate_decision_context(
        base_decision(asset="ETH/USD"),
        profile=profile(),
        market={"last_close": 100},
        derivatives=derivatives(),
        config=context_config(),
    )
    assert result.decision.decision == "NO_TRADE"


def test_wrong_horizon_falls_back_to_no_trade() -> None:
    result = validate_decision_context(
        base_decision(horizon="4h"),
        profile=profile(),
        market={"last_close": 100},
        derivatives=derivatives(),
        config=context_config(),
    )
    assert result.decision.decision == "NO_TRADE"


def test_entry_price_too_far_falls_back_to_no_trade() -> None:
    result = validate_decision_context(
        base_decision(reference_entry_price=110),
        profile=profile(),
        market={"last_close": 100},
        derivatives=derivatives(),
        config=context_config(),
    )
    assert result.decision.decision == "NO_TRADE"


def test_unavailable_critical_data_falls_back_to_no_trade() -> None:
    result = validate_decision_context(
        base_decision(critical_data_used=["price", "funding"]),
        profile=profile(),
        market={"last_close": 100},
        derivatives=derivatives(),
        config=context_config(),
    )
    assert result.decision.decision == "NO_TRADE"

