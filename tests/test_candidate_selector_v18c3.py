from __future__ import annotations

from pathlib import Path

import pandas as pd

from galapagos.agent.decision_context import build_decision_context
from galapagos.backtest.candidate_selector import select_candidate_setups


def test_candidate_selector_finds_candidates_on_mock_data(tmp_path: Path) -> None:
    data_path = _write_breakout_data(tmp_path)
    profile = _profile()
    candidates = select_candidate_setups(
        profile=profile,
        data_path=data_path,
        source_policies=["state_aware_breakout", "state_aware_momentum"],
        max_candidates=3,
        warmup_bars=25,
        min_spacing_bars=1,
    )
    assert candidates
    assert all(candidate.context_index >= 24 for candidate in candidates)
    assert all(candidate.baseline_decision in {"LONG", "SHORT"} for candidate in candidates)


def test_decision_context_contains_candidate_setup() -> None:
    ctx = build_decision_context(
        profile=_profile(),
        market={"last_close": 100, "last_high": 101, "last_low": 99},
        indicators={"sma_20": 99, "sma_50": 98, "market_regime": {}},
        derivatives={"funding": {"status": "unavailable"}},
        scenarios=[],
        portfolio={"current_position": None, "current_price": 100},
        risk_config={"max_risk_per_trade": 0.005},
        decision_timestamp="2026-01-01T00:00:00+00:00",
        data_mode="test",
        run_id="run",
        candidate_setup={
            "baseline_policy": "state_aware_breakout",
            "baseline_decision": "LONG",
            "baseline_strategy": "breakout",
            "current_price": 100.0,
            "suggested_stop_loss": 99.0,
            "suggested_take_profit": 102.0,
            "baseline_reason_summary": "Mock setup",
        },
    )
    payload = ctx.to_dict()
    assert payload["candidate_setup"]["exists"] is True
    assert payload["candidate_setup"]["proposed_decision"] == "LONG"
    assert "validate or refuse" in payload["candidate_setup"]["instruction"]
    assert payload["available_critical_data"]["price"] is True
    assert payload["available_critical_data"]["volatility"] is False
    assert payload["available_critical_data"]["candidate_setup"] is True
    assert payload["costs"]["estimated_fee_rate"] == 0.001
    assert payload["costs"]["estimated_slippage_bps"] == 5.0
    assert payload["costs"]["estimated_round_trip_cost"] > 0
    assert payload["costs"]["candidate_expected_move"] == 0.02


def _write_breakout_data(tmp_path: Path) -> Path:
    rows = []
    start = pd.Timestamp("2026-01-01T00:00:00Z")
    price = 100.0
    for index in range(40):
        if index > 25:
            price += 2.0
        rows.append(
            {
                "timestamp": start + pd.Timedelta(hours=4 * index),
                "open": price - 0.5,
                "high": price + 1.0,
                "low": price - 1.0,
                "close": price,
                "volume": 10 + index,
            }
        )
    path = tmp_path / "ohlcv.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _profile() -> dict:
    return {
        "name": "galapagos_4h",
        "symbol": "BTC/USD",
        "timeframe": "4h",
        "paper_trading_only": True,
        "max_position_duration_minutes": 1440,
    }
