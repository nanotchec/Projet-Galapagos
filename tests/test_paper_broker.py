from galapagos.agent.decision_schema import AgentDecision
from galapagos.execution.fee_model import FeeModel
from galapagos.execution.paper_broker import PaperBroker
from galapagos.execution.slippage_model import SlippageModel


def test_paper_broker_applies_entry_fee_and_slippage() -> None:
    broker = PaperBroker(
        initial_capital=10_000,
        fee_model=FeeModel(0.001),
        slippage_model=SlippageModel(10),
    )
    decision = AgentDecision(
        decision="LONG",
        profile="galapagos_30m",
        asset="BTC/USD",
        strategy="breakout",
        confidence=0.6,
        reasoning_summary="Breakout.",
        horizon="30m",
        reference_entry_price=100,
        stop_loss=95,
        take_profit=110,
        risk_fraction=0.005,
        max_duration_minutes=240,
        invalidation_conditions=[],
        critical_data_used=["price", "volatility"],
    )
    event = broker.execute_decision(decision, approved_risk_fraction=0.005)
    position = event["position"]
    assert position["entry_price"] == 100.1
    assert position["entry_fee"] > 0
    assert position["entry_slippage"] > 0

