from __future__ import annotations

from galapagos.agent.decision_schema import AgentDecision, DecisionType, StrategyType
from galapagos.execution.exit_policy import apply_exit_policy


def test_close_becomes_hold_before_min_holding_bars() -> None:
    result = apply_exit_policy(
        _close_decision(),
        portfolio={"has_open_position": True, "bars_in_position": 2},
        config=_config(),
    )

    assert result.decision.decision == DecisionType.HOLD
    assert result.exit_policy_override == "agent_close_delayed"
    assert result.original_decision == "CLOSE"
    assert result.final_decision == "HOLD"
    assert result.bars_in_position == 2
    assert result.min_holding_bars == 3


def test_close_allowed_after_min_holding_bars() -> None:
    decision = _close_decision()
    result = apply_exit_policy(
        decision,
        portfolio={"has_open_position": True, "bars_in_position": 3},
        config=_config(),
    )

    assert result.decision is decision
    assert result.exit_policy_override is None


def test_non_close_decisions_are_not_blocked() -> None:
    for decision in (_hold_decision(), _long_decision()):
        result = apply_exit_policy(
            decision,
            portfolio={"has_open_position": True, "bars_in_position": 1},
            config=_config(),
        )
        assert result.decision is decision
        assert result.action == "unchanged"


def test_force_close_at_end_priority_is_outside_agent_exit_policy() -> None:
    result = apply_exit_policy(
        _close_decision(),
        portfolio={"has_open_position": True, "bars_in_position": 1},
        config={"holding_aware": {"enabled": False}},
    )

    assert result.decision.decision == DecisionType.CLOSE
    assert result.exit_policy_override is None


def test_stop_loss_and_take_profit_priority_remain_broker_responsibility() -> None:
    result = apply_exit_policy(
        _hold_decision(),
        portfolio={"has_open_position": True, "bars_in_position": 1},
        config=_config(),
    )

    assert result.decision.decision == DecisionType.HOLD
    assert result.exit_policy_override is None


def _config() -> dict:
    return {
        "holding_aware": {
            "enabled": True,
            "min_holding_bars_before_agent_close": 3,
            "agent_close_before_min_policy": "convert_to_hold",
            "stop_loss_priority": True,
            "take_profit_priority": True,
            "max_duration_priority": True,
        }
    }


def _close_decision() -> AgentDecision:
    return AgentDecision(
        decision=DecisionType.CLOSE,
        profile="galapagos_4h",
        asset="BTC/USD",
        strategy=StrategyType.CLOSE_POSITION,
        confidence=0.6,
        reasoning_summary="Close invalidated position.",
        horizon="4h",
        reference_entry_price=None,
        stop_loss=None,
        take_profit=None,
        risk_fraction=0.0,
        max_duration_minutes=0,
        invalidation_conditions=[],
        critical_data_used=[],
    )


def _hold_decision() -> AgentDecision:
    return AgentDecision(
        decision=DecisionType.HOLD,
        profile="galapagos_4h",
        asset="BTC/USD",
        strategy=StrategyType.RISK_REDUCTION,
        confidence=0.5,
        reasoning_summary="Hold position.",
        horizon="4h",
        reference_entry_price=None,
        stop_loss=None,
        take_profit=None,
        risk_fraction=0.0,
        max_duration_minutes=0,
        invalidation_conditions=[],
        critical_data_used=[],
    )


def _long_decision() -> AgentDecision:
    return AgentDecision(
        decision=DecisionType.LONG,
        profile="galapagos_4h",
        asset="BTC/USD",
        strategy=StrategyType.MOMENTUM,
        confidence=0.6,
        reasoning_summary="Long setup.",
        horizon="4h",
        reference_entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        risk_fraction=0.003,
        max_duration_minutes=960,
        invalidation_conditions=["invalidated"],
        critical_data_used=["price", "volatility"],
        setup_quality="acceptable",
    )
