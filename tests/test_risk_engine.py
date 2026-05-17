import pytest
from pydantic import ValidationError

from galapagos.agent.decision_schema import AgentDecision
from galapagos.risk.risk_engine import RiskEngine


def risk_config() -> dict:
    return {
        "max_risk_per_trade": 0.005,
        "max_daily_loss": 0.02,
        "max_weekly_loss": 0.05,
        "max_trades_per_day": 6,
        "stop_loss_required": True,
        "take_profit_or_time_exit_required": True,
        "kill_switch_enabled": True,
        "required_critical_data": ["price", "volatility"],
    }


def profile() -> dict:
    return {"paper_trading_only": True, "max_trades_per_day": 6}


def test_risk_engine_refuses_long_without_stop_loss() -> None:
    with pytest.raises(ValidationError):
        AgentDecision(
            decision="LONG",
            profile="galapagos_30m",
            asset="BTC/USD",
            strategy="breakout",
            confidence=0.6,
            reasoning_summary="Breakout.",
            horizon="30m",
            reference_entry_price=65000,
            stop_loss=None,
            take_profit=66000,
            risk_fraction=0.002,
            max_duration_minutes=240,
            invalidation_conditions=[],
            critical_data_used=["price", "volatility"],
        )


def test_risk_engine_refuses_risk_fraction_too_high() -> None:
    decision = AgentDecision(
        decision="LONG",
        profile="galapagos_30m",
        asset="BTC/USD",
        strategy="breakout",
        confidence=0.6,
        reasoning_summary="Breakout.",
        horizon="30m",
        reference_entry_price=65000,
        stop_loss=64000,
        take_profit=67000,
        risk_fraction=0.02,
        max_duration_minutes=240,
        invalidation_conditions=[],
        critical_data_used=["price", "volatility"],
    )
    result = RiskEngine(risk_config()).evaluate(decision, profile_config=profile())
    assert not result.approved
    assert "risk_fraction exceeds max_risk_per_trade" in result.reasons

