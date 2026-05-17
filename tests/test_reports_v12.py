import json
from datetime import UTC, datetime

from galapagos.analysis.profile_comparison import generate_profile_comparison_report
from galapagos.journal.sqlite_store import SQLiteStore
from galapagos.reports.daily_report import generate_daily_summary
from galapagos.utils.paths import PROJECT_ROOT


def test_compare_profiles_generates_result(tmp_path) -> None:
    store = seeded_store(tmp_path / "galapagos.sqlite")
    paths = generate_profile_comparison_report(store, tmp_path)
    assert paths["markdown"].exists()
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["rows"][0]["profile"] == "galapagos_30m"
    assert "avg_trade_pnl" in payload["rows"][0]


def test_daily_summary_contains_essential_metrics(tmp_path) -> None:
    store = seeded_store(tmp_path / "galapagos.sqlite")
    paths = generate_daily_summary(store, tmp_path)
    content = paths["markdown"].read_text(encoding="utf-8")
    assert "Cycles executes" in content
    assert "Realized PnL" in content
    assert "Disponibilite derivees" in content


def test_zip_instructions_are_present_in_runbook() -> None:
    content = (PROJECT_ROOT / "docs/runbook.md").read_text(encoding="utf-8")
    assert "COPYFILE_DISABLE=1 zip -r projet-galapagos-v1.4-clean.zip" in content
    assert "zipinfo -1 projet-galapagos-v1.4-clean.zip" in content


def seeded_store(path) -> SQLiteStore:
    store = SQLiteStore(path)
    now = datetime.now(UTC).isoformat()
    snapshot_id = store.insert_market_snapshot(
        {
            "timestamp_utc": now,
            "profile": "galapagos_30m",
            "asset": "BTC/USD",
            "timeframe": "30m",
            "market": {"last_close": 100, "source": "mock_ohlcv"},
            "indicators": {},
            "derivatives": {
                "funding": {"status": "unavailable"},
                "open_interest": {"status": "unavailable"},
            },
            "scenarios": [],
            "data_quality": {"status": "available"},
        }
    )
    store.insert_agent_decision(
        {
            "timestamp_utc": now,
            "profile": "galapagos_30m",
            "asset": "BTC/USD",
            "timeframe": "30m",
            "input_context_hash": "hash",
            "market_snapshot_id": snapshot_id,
            "raw_llm_response": "{}",
            "parsed_decision": {"decision": "NO_TRADE"},
            "decision_validity": "valid_schema",
            "risk_engine_result": {"approved": False},
            "final_action": "NO_TRADE",
            "reasoning_summary": "No trade.",
            "critical_data_used": [],
        }
    )
    store.insert_paper_trade(
        {
            "entry_timestamp": now,
            "exit_timestamp": now,
            "side": "LONG",
            "entry_price": 100,
            "exit_price": 105,
            "stop_loss": 95,
            "take_profit": 110,
            "size": 1,
            "fees": 0.2,
            "slippage": 0.1,
            "pnl": 4.7,
            "pnl_percent": 0.047,
            "strategy": "breakout",
            "profile": "galapagos_30m",
            "status": "CLOSED",
            "close_reason": "take_profit",
        }
    )
    store.insert_performance_snapshot(
        {
            "timestamp_utc": now,
            "profile": "galapagos_30m",
            "cash": 10_004.7,
            "equity": 10_004.7,
            "metrics": {},
        }
    )
    return store
