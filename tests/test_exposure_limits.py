from datetime import UTC, datetime

from galapagos.agent.decision_schema import AgentDecision
from galapagos.execution.position_manager import Position
from galapagos.risk.risk_engine import RiskEngine


def test_max_open_positions_blocks_new_trade() -> None:
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
        risk_fraction=0.002,
        max_duration_minutes=240,
        invalidation_conditions=[],
        critical_data_used=["price", "volatility"],
    )
    existing = Position(
        id="pos-1",
        profile="galapagos_30m",
        asset="BTC/USD",
        side="LONG",
        entry_price=100,
        size=1,
        stop_loss=95,
        take_profit=110,
        max_duration_minutes=240,
        strategy="breakout",
        entry_timestamp=datetime.now(UTC).isoformat(),
        entry_fee=0,
        entry_slippage=0,
    )
    result = RiskEngine(
        {
            "max_risk_per_trade": 0.005,
            "max_daily_loss": 0.02,
            "max_weekly_loss": 0.05,
            "max_trades_per_day": 6,
            "stop_loss_required": True,
            "take_profit_or_time_exit_required": True,
            "kill_switch_enabled": True,
            "required_critical_data": ["price", "volatility"],
            "max_open_positions_global": 1,
            "max_open_positions_per_profile": 1,
            "allow_multiple_positions_same_asset": False,
            "max_total_exposure_fraction": 1.0,
        }
    ).evaluate(
        decision,
        profile_config={"paper_trading_only": True, "max_trades_per_day": 6},
        open_positions=[existing],
        current_price=100,
        current_capital=10_000,
    )
    assert not result.approved
    assert "Max open positions global reached" in result.reasons

