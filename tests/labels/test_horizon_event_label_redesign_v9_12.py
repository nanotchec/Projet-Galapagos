from __future__ import annotations

import pandas as pd

from galapagos.labels.horizon_event_label_redesign_v9_12 import (
    build_horizon_event_label_frame_v9_12,
    decide_v9_12,
    event_based_safety_guard_v9_12,
    forbidden_output_scan_v9_12,
    horizon_bars_v9_12,
    leakage_guard_v9_12,
)
from galapagos.labels.horizon_event_label_redesign_v9_12_schemas import (
    HORIZON_EVENT_LABEL_COLUMNS_V9_12,
)


def _sample_dataset(rows: int = 600) -> pd.DataFrame:
    ts = pd.date_range("2023-03-25", periods=rows, freq="min", tz="UTC")
    close = pd.Series([100.0 + (index * 0.01) + ((index % 17) * 0.001) for index in range(rows)])
    return pd.DataFrame(
        {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "event_ts": ts,
            "close_ts": ts,
            "decision_ts": ts,
            "close": close,
            "warmup_row": False,
            "split": ["train"] * 360 + ["validation"] * 120 + ["test"] * 120,
            "walk_forward_group": ts.strftime("%Y-%m"),
        }
    )


def test_horizon_event_schema_and_targets_v9_12() -> None:
    frame = build_horizon_event_label_frame_v9_12(
        _sample_dataset(),
        source_dataset_version="V9.7",
        label_run_id="test",
        selected_horizon="h4",
        selected_multiplier=1.25,
        event_multiplier=3.0,
    )

    assert list(frame.columns) == HORIZON_EVENT_LABEL_COLUMNS_V9_12
    assert frame["target_name"].dropna().unique().tolist() == ["up_down_flat_volnorm_h4"]
    assert {"up_down_flat_volnorm_h2", "up_down_flat_volnorm_h4", "up_down_flat_volnorm_h8"}.issubset(frame.columns)
    assert "event_based_label" in frame.columns


def test_horizon_bars_are_duration_based_v9_12() -> None:
    assert horizon_bars_v9_12("1m", "h2") == 120
    assert horizon_bars_v9_12("5m", "h4") == 48
    assert horizon_bars_v9_12("15m", "h8") == 32
    assert horizon_bars_v9_12("1h", "h8") == 8


def test_no_forbidden_outputs_or_event_backtest_v9_12() -> None:
    assert forbidden_output_scan_v9_12()["passed"] is True
    safety = event_based_safety_guard_v9_12()
    assert safety["passed"] is True
    assert safety["no_entry"] is True
    assert safety["no_exit"] is True
    assert safety["no_pnl"] is True
    assert safety["no_backtest"] is True


def test_leakage_guard_requires_temporal_availability_v9_12() -> None:
    guard = leakage_guard_v9_12()

    assert guard["passed"] is True
    assert guard["causal_volatility_uses_only_past_closed_returns"] is True
    assert guard["future_returns_used_only_for_labels"] is True
    assert guard["label_available_ts_after_decision_ts_required"] is True


def test_decision_requires_review_when_event_warnings_exist_v9_12() -> None:
    decision = decide_v9_12(
        "PASS",
        {"1m": {"errors": [], "warnings": []}},
        {"status": "requires_review", "warnings": ["1m: AMBIGUOUS dominates this timeframe"]},
    )

    assert decision == "label_redesign_candidate_horizon_event_created_requires_review"
