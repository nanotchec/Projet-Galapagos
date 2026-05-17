from datetime import UTC, datetime, timedelta

from galapagos.agent.decision_schema import AgentDecision
from galapagos.cycle import run_cycle
from galapagos.execution.paper_broker import PaperBroker
from galapagos.execution.paper_state import PaperState
from galapagos.execution.position_manager import Position
from galapagos.journal.sqlite_store import SQLiteStore


def profile() -> dict:
    return {
        "name": "galapagos_30m",
        "symbol": "BTC/USD",
        "timeframe": "30m",
        "paper_trading_only": True,
        "max_trades_per_day": 6,
        "max_position_duration_minutes": 240,
    }


def risk_config(**overrides) -> dict:
    config = {
        "simulated_initial_capital": 10_000,
        "max_risk_per_trade": 0.005,
        "max_daily_loss": 0.02,
        "max_weekly_loss": 0.05,
        "max_trades_per_day": 6,
        "stop_loss_required": True,
        "take_profit_or_time_exit_required": True,
        "kill_switch_enabled": True,
        "required_critical_data": ["price", "volatility"],
        "max_open_positions_global": 2,
        "max_open_positions_per_profile": 1,
        "allow_multiple_positions_same_asset": False,
        "max_total_exposure_fraction": 1.0,
    }
    config.update(overrides)
    return config


def test_risk_rejected_does_not_create_position(tmp_path) -> None:
    db = tmp_path / "galapagos.sqlite"
    result = run_cycle(
        profile=profile(),
        risk_config=risk_config(max_risk_per_trade=0.001),
        llm_config={},
        database_path=str(db),
        use_mock_llm=True,
        mock_decision="LONG",
    )
    store = SQLiteStore(db)
    assert result["execution"]["action"] == "RISK_REJECTED"
    assert store.query("SELECT COUNT(*) AS count FROM positions")[0]["count"] == 0


def test_position_persists_between_cycles(tmp_path) -> None:
    db = tmp_path / "galapagos.sqlite"
    run_cycle(
        profile=profile(),
        risk_config=risk_config(),
        llm_config={},
        database_path=str(db),
        use_mock_llm=True,
        mock_decision="LONG",
    )
    broker = PaperState(
        SQLiteStore(db),
        initial_capital=10_000,
        profile="galapagos_30m",
    ).load_broker()
    assert len(broker.positions) == 1


def test_stop_loss_closes_long() -> None:
    broker = broker_with_position(side="LONG", stop_loss=95, take_profit=110)
    events = broker.evaluate_position_exits(candle={"high": 104, "low": 94, "close": 100})
    assert events[0]["trade"]["close_reason"] == "stop_loss"
    assert not broker.positions


def test_take_profit_closes_long() -> None:
    broker = broker_with_position(side="LONG", stop_loss=95, take_profit=110)
    events = broker.evaluate_position_exits(candle={"high": 111, "low": 99, "close": 110})
    assert events[0]["trade"]["close_reason"] == "take_profit"


def test_stop_loss_closes_short() -> None:
    broker = broker_with_position(side="SHORT", stop_loss=105, take_profit=90)
    events = broker.evaluate_position_exits(candle={"high": 106, "low": 99, "close": 104})
    assert events[0]["trade"]["close_reason"] == "stop_loss"


def test_take_profit_closes_short() -> None:
    broker = broker_with_position(side="SHORT", stop_loss=105, take_profit=90)
    events = broker.evaluate_position_exits(candle={"high": 101, "low": 89, "close": 90})
    assert events[0]["trade"]["close_reason"] == "take_profit"


def test_stop_wins_when_stop_and_take_profit_touched_same_candle() -> None:
    broker = broker_with_position(side="LONG", stop_loss=95, take_profit=110)
    events = broker.evaluate_position_exits(candle={"high": 111, "low": 94, "close": 100})
    assert events[0]["trade"]["close_reason"] == "stop_loss"


def test_max_duration_closes_position() -> None:
    broker = broker_with_position(side="LONG", stop_loss=95, take_profit=110)
    position = next(iter(broker.positions.values()))
    position.entry_timestamp = (datetime.now(UTC) - timedelta(minutes=300)).isoformat()
    events = broker.evaluate_position_exits(candle={"high": 104, "low": 99, "close": 101})
    assert events[0]["trade"]["close_reason"] == "max_duration"


def test_close_closes_existing_position() -> None:
    broker = broker_with_position(side="LONG", stop_loss=95, take_profit=110)
    decision = close_decision()
    event = broker.execute_decision(decision, approved_risk_fraction=0, current_price=101)
    assert event["action"] == "CLOSE_POSITION"
    assert event["trade"]["close_reason"] == "agent_close"
    assert not broker.positions


def test_close_ignored_without_open_position() -> None:
    broker = PaperBroker(initial_capital=10_000)
    event = broker.execute_decision(close_decision(), approved_risk_fraction=0, current_price=101)
    assert event == {"action": "CLOSE_IGNORED", "status": "NO_OPEN_POSITION"}


def broker_with_position(side: str, stop_loss: float, take_profit: float) -> PaperBroker:
    entry_time = (datetime.now(UTC) - timedelta(minutes=30)).isoformat()
    position = Position(
        id="pos-1",
        profile="galapagos_30m",
        asset="BTC/USD",
        side=side,
        entry_price=100,
        size=1,
        stop_loss=stop_loss,
        take_profit=take_profit,
        max_duration_minutes=240,
        strategy="breakout",
        entry_timestamp=entry_time,
        entry_fee=0,
        entry_slippage=0,
    )
    return PaperBroker(initial_capital=10_000, positions={position.id: position})


def close_decision() -> AgentDecision:
    return AgentDecision(
        decision="CLOSE",
        profile="galapagos_30m",
        asset="BTC/USD",
        strategy="close_position",
        confidence=0.7,
        reasoning_summary="Close existing paper position.",
        horizon="30m",
        reference_entry_price=None,
        stop_loss=None,
        take_profit=None,
        risk_fraction=0,
        max_duration_minutes=0,
        invalidation_conditions=[],
        critical_data_used=[],
    )
