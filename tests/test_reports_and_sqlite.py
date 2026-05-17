from galapagos.cycle import run_cycle
from galapagos.journal.sqlite_store import SQLiteStore
from galapagos.reports.daily_report import generate_daily_report


def test_report_markdown_and_sqlite_decision_trade(tmp_path) -> None:
    db = tmp_path / "galapagos.sqlite"
    result = run_cycle(
        profile={
            "name": "galapagos_30m",
            "symbol": "BTC/USD",
            "timeframe": "30m",
            "paper_trading_only": True,
            "max_trades_per_day": 6,
            "max_position_duration_minutes": 240,
        },
        risk_config={
            "simulated_initial_capital": 10_000,
            "max_risk_per_trade": 0.005,
            "max_daily_loss": 0.02,
            "max_weekly_loss": 0.05,
            "max_trades_per_day": 6,
            "stop_loss_required": True,
            "take_profit_or_time_exit_required": True,
            "kill_switch_enabled": True,
            "required_critical_data": ["price", "volatility"],
        },
        llm_config={},
        database_path=str(db),
        use_mock_llm=True,
        mock_decision="LONG",
    )
    paths = generate_daily_report(result, tmp_path)
    assert paths["markdown"].exists()
    store = SQLiteStore(db)
    assert store.query("SELECT COUNT(*) AS count FROM agent_decisions")[0]["count"] == 1
    assert store.query("SELECT COUNT(*) AS count FROM positions")[0]["count"] == 1

