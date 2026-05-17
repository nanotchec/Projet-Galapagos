from galapagos.agent.decision_parser import parse_decision_response
from galapagos.agent.decision_schema import AgentDecision


def test_valid_decision_schema() -> None:
    decision = AgentDecision(
        decision="NO_TRADE",
        profile="galapagos_30m",
        asset="BTC/USD",
        strategy="no_trade",
        confidence=0.55,
        reasoning_summary="No edge.",
        horizon="30m",
        reference_entry_price=None,
        stop_loss=None,
        take_profit=None,
        risk_fraction=0.0,
        max_duration_minutes=0,
        invalidation_conditions=[],
        critical_data_used=[],
    )
    assert decision.decision == "NO_TRADE"


def test_invalid_json_falls_back_to_no_trade() -> None:
    decision = parse_decision_response("{bad json", "galapagos_30m", "BTC/USD", "30m")
    assert decision.decision == "NO_TRADE"
    assert decision.strategy == "no_trade"

