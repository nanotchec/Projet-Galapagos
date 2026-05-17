from galapagos.cycle import run_cycle
from galapagos.journal.sqlite_store import SQLiteStore


def profile(name: str, timeframe: str) -> dict:
    return {
        "name": name,
        "symbol": "BTC/USD",
        "timeframe": timeframe,
        "paper_trading_only": True,
        "max_trades_per_day": 6,
        "max_position_duration_minutes": 240,
    }


def risk_config() -> dict:
    return {
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


def test_cash_is_separate_by_profile(tmp_path) -> None:
    db = tmp_path / "galapagos.sqlite"
    run_cycle(
        profile=profile("galapagos_30m", "30m"),
        risk_config=risk_config(),
        llm_config={},
        database_path=str(db),
        use_mock_llm=True,
        mock_decision="LONG",
    )
    store = SQLiteStore(db)
    cash_30m = store.get_account_cash(10_000, profile="galapagos_30m")
    cash_4h = store.get_account_cash(10_000, profile="galapagos_4h")
    assert cash_30m < 10_000
    assert cash_4h == 10_000


def test_position_30m_does_not_block_4h_position(tmp_path) -> None:
    db = tmp_path / "galapagos.sqlite"
    config = risk_config()
    first = run_cycle(
        profile=profile("galapagos_30m", "30m"),
        risk_config=config,
        llm_config={},
        database_path=str(db),
        use_mock_llm=True,
        mock_decision="LONG",
    )
    second = run_cycle(
        profile=profile("galapagos_4h", "4h"),
        risk_config=config,
        llm_config={},
        database_path=str(db),
        use_mock_llm=True,
        mock_decision="LONG",
    )
    assert first["risk"]["approved"]
    assert second["risk"]["approved"]
    store = SQLiteStore(db)
    positions = store.load_open_positions()
    assert {position["profile"] for position in positions} == {"galapagos_30m", "galapagos_4h"}

