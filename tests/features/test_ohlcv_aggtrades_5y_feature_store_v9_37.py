from __future__ import annotations

from pathlib import Path

import pandas as pd

from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_37 import (
    build_timeframe_features_v9_37,
    date_range_v9_37,
    validate_feature_frame_v9_37,
)
from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_37_schemas import (
    FEATURE_COLUMNS,
    FORBIDDEN_FEATURE_COLUMNS,
    STRICT_COLUMNS,
)


def test_v9_37_target_window_has_expected_days() -> None:
    assert len(date_range_v9_37("2021-05-05", "2026-05-05")) == 1827


def test_v9_37_feature_builder_uses_strict_schema_and_no_forbidden_columns() -> None:
    frame = _sample_ohlcv_frame(rows=80)

    features = build_timeframe_features_v9_37(frame, timeframe="1m", feature_run_id="test_run")

    assert list(features.columns) == STRICT_COLUMNS
    assert set(features.columns).isdisjoint(FORBIDDEN_FEATURE_COLUMNS)
    assert len(FEATURE_COLUMNS) == 41
    assert features["feature_available_ts"].le(features["decision_ts"]).all()
    assert features["row_valid_for_features"].all()


def test_v9_37_feature_builder_marks_warmup_and_zero_trade_rows() -> None:
    frame = _sample_ohlcv_frame(rows=80)
    frame.loc[10, ["volume", "quote_volume", "trades_count", "taker_buy_base_volume", "taker_buy_quote_volume"]] = 0

    features = build_timeframe_features_v9_37(frame, timeframe="1m", feature_run_id="test_run")

    assert int(features["warmup_row"].sum()) > 0
    assert bool(features.loc[10, "zero_trade_bucket"]) is True
    assert features.loc[10, "average_trade_size"] == 0
    assert features.loc[10, "taker_buy_sell_imbalance"] == 0


def test_v9_37_validator_accepts_small_valid_feature_frame_when_row_expectation_matches(tmp_path) -> None:
    frame = _sample_ohlcv_frame(rows=80)
    features = build_timeframe_features_v9_37(frame, timeframe="1m", feature_run_id="test_run")
    path = tmp_path / "features.parquet"

    result = validate_feature_frame_v9_37(features, timeframe="1m", path=path)

    assert result["strict_schema_status"] == "PASS"
    assert result["forbidden_columns"] == []
    assert result["feature_available_ts_lte_decision_ts"] is True
    assert result["available_ts_lte_decision_ts"] is True
    assert result["quality_status"] == "FAIL"
    assert any("actual_rows_mismatch" in error for error in result["errors"])


def test_v9_37_features_do_not_use_placeholder_test_bodies() -> None:
    source = Path(__file__).read_text(encoding="utf-8")

    assert "pass\n" not in source
    assert ("assert " + "True") not in source


def _sample_ohlcv_frame(rows: int) -> pd.DataFrame:
    open_ts = pd.date_range("2021-05-05T00:00:00Z", periods=rows, freq="min")
    close_ts = open_ts + pd.Timedelta(minutes=1) - pd.Timedelta(milliseconds=1)
    close = pd.Series([100.0 + index * 0.1 for index in range(rows)])
    return pd.DataFrame(
        {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "ohlcv_source_type": "derived_from_aggtrades",
            "open_ts": open_ts,
            "close_ts": close_ts,
            "event_ts": open_ts,
            "decision_ts": close_ts,
            "available_ts": close_ts,
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close + 0.5,
            "volume": pd.Series([10.0] * rows),
            "quote_volume": pd.Series([1000.0] * rows),
            "trades_count": pd.Series([5] * rows),
            "taker_buy_base_volume": pd.Series([4.0] * rows),
            "taker_buy_quote_volume": pd.Series([400.0] * rows),
            "source_aggtrades_window_start": pd.Timestamp("2021-05-05T00:00:00Z"),
            "source_aggtrades_window_end": pd.Timestamp("2026-05-05T23:59:59.999Z"),
            "source_aggtrades_validation_version": "V9.32",
            "row_valid": True,
            "invalid_reason": "",
            "derivation_run_id": "test",
            "ohlcv_schema_version": "test",
        }
    )
