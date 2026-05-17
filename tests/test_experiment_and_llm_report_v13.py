import json

from galapagos.journal.sqlite_store import SQLiteStore
from galapagos.reports.llm_decisions_report import generate_llm_decisions_report
from galapagos.utils.config_loader import load_yaml


def test_experiment_config_loads() -> None:
    experiment = load_yaml("configs/experiments/btc_30m_vs_4h.yaml")
    assert experiment["experiment_name"] == "btc_30m_vs_4h"
    assert experiment["profiles"] == ["30m", "4h"]


def test_llm_decisions_report_generated(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "galapagos.sqlite")
    now = "2026-04-24T00:00:00+00:00"
    store.insert_agent_decision(
        {
            "timestamp_utc": now,
            "profile": "galapagos_30m",
            "asset": "BTC/USD",
            "timeframe": "30m",
            "input_context_hash": "hash",
            "market_snapshot_id": None,
            "raw_llm_response": "{bad json",
            "parsed_decision": {"decision": "NO_TRADE", "confidence": 0.0},
            "decision_validity": "parser_fallback",
            "risk_engine_result": {"approved": False, "reasons": ["Invalid LLM"]},
            "final_action": "NO_TRADE",
            "reasoning_summary": "Fallback.",
            "critical_data_used": [],
        }
    )
    paths = generate_llm_decisions_report(store, tmp_path)
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["parser_fallback"] == 1
    assert payload["no_trade_rate"] == 1.0

