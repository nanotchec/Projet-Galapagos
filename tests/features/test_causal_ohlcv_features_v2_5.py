from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from galapagos.features.causal_ohlcv import build_causal_features
from galapagos.features.schemas import FEATURE_COLUMNS_V2_5, FORBIDDEN_TERMS


def test_build_features_row_count_matches_input() -> None:
    frame = _frame_1m(60)
    features = build_causal_features(frame, "ohlcv-sha", "run-v2.5")
    assert len(features) == len(frame)


def test_build_features_strict_columns() -> None:
    frame = _frame_1m(60)
    features = build_causal_features(frame, "ohlcv-sha", "run-v2.5")
    assert list(features.columns) == FEATURE_COLUMNS_V2_5


def test_returns_are_past_only() -> None:
    # A positive shift would look into the future, we ensure features use past values.
    frame = _frame_1m(60)
    features = build_causal_features(frame, "ohlcv-sha", "run-v2.5")
    
    # close_lag_1 at index 1 must match close at index 0
    assert features.loc[1, "close_lag_1"] == pytest.approx(frame.loc[0, "close"])
    assert pd.isna(features.loc[0, "close_lag_1"])


def test_rolling_features_have_expected_warmup() -> None:
    # rolling features like sma_30 or rolling_vol_30 need min_periods=30, so the first 30 lines (indices 0 to 29) must be warmup
    frame = _frame_1m(60)
    features = build_causal_features(frame, "ohlcv-sha", "run-v2.5")
    
    assert features.loc[:29, "warmup_row"].all()
    assert not features.loc[30, "warmup_row"]
    
    # Warmup null count check
    assert features.loc[0, "feature_null_count"] > 0
    assert features.loc[30, "feature_null_count"] == 0


def test_temporal_features_utc() -> None:
    frame = _frame_1m(60)
    features = build_causal_features(frame, "ohlcv-sha", "run-v2.5")
    
    # Event ts hours
    assert features.loc[0, "hour_utc"] == 0
    assert features.loc[0, "day_of_week_utc"] == 0  # 2024-01-15 is Monday (0)
    assert not features.loc[0, "is_weekend_utc"]


def test_feature_available_ts_not_before_available_ts() -> None:
    frame = _frame_1m(60)
    features = build_causal_features(frame, "ohlcv-sha", "run-v2.5")
    
    avail = pd.to_datetime(features["available_ts"], utc=True)
    feat_avail = pd.to_datetime(features["feature_available_ts"], utc=True)
    
    assert (feat_avail >= avail).all()


def test_decision_ts_not_before_feature_available_ts() -> None:
    frame = _frame_1m(60)
    features = build_causal_features(frame, "ohlcv-sha", "run-v2.5")
    
    feat_avail = pd.to_datetime(features["feature_available_ts"], utc=True)
    dec = pd.to_datetime(features["decision_ts"], utc=True)
    
    assert (dec >= feat_avail).all()


def test_no_forbidden_feature_columns() -> None:
    frame = _frame_1m(60)
    features = build_causal_features(frame, "ohlcv-sha", "run-v2.5")
    
    for col in features.columns:
        if col in FEATURE_COLUMNS_V2_5:
            continue
        for term in FORBIDDEN_TERMS:
            assert term not in col.lower(), f"column {col} matches forbidden term {term}"


def test_candle_position_in_range_flat_candle() -> None:
    # Test flat candle (high == low) to ensure no division by zero error occurs
    frame = _frame_1m(5)
    frame.loc[0, "high"] = 100.0
    frame.loc[0, "low"] = 100.0
    frame.loc[0, "close"] = 100.0
    frame.loc[0, "open"] = 100.0
    
    features = build_causal_features(frame, "ohlcv-sha", "run-v2.5")
    assert features.loc[0, "close_position_in_range"] == 0.0


def _frame_1m(rows: int) -> pd.DataFrame:
    start = pd.Timestamp("2024-01-15T00:00:00Z")
    records = []
    for index in range(rows):
        event_ts = start + pd.Timedelta(minutes=index)
        close_ts = event_ts + pd.Timedelta(seconds=59, milliseconds=999)
        open_price = 42000.0 + index
        records.append(
            {
                "source": "binance_archive",
                "venue": "binance",
                "market_type": "spot",
                "symbol": "BTCUSDT",
                "timeframe": "1m",
                "event_ts": event_ts,
                "close_ts": close_ts,
                "available_ts": close_ts,
                "decision_ts": close_ts,
                "ingested_at_ts": pd.Timestamp("2026-05-19T00:00:00Z"),
                "open": open_price,
                "high": open_price + 10.0,
                "low": open_price - 10.0,
                "close": open_price + 1.0,
                "volume": 2.0 + index / 1000,
                "quote_volume": 10.0 + index,
                "trade_count": 100 + index,
                "taker_buy_base_volume": 1.0,
                "taker_buy_quote_volume": 5.0,
                "source_open_time_raw": int(event_ts.timestamp() * 1000),
                "source_close_time_raw": int(close_ts.timestamp() * 1000),
                "source_timestamp_unit": "ms",
                "raw_file_sha256": "raw-sha",
                "ingestion_run_id": "run-id",
            }
        )
    # The V2.4 OHLCV columns list
    ohlcv_columns = [
        "source", "venue", "market_type", "symbol", "timeframe", "event_ts",
        "close_ts", "available_ts", "decision_ts", "ingested_at_ts",
        "open", "high", "low", "close", "volume", "quote_volume", "trade_count",
        "taker_buy_base_volume", "taker_buy_quote_volume", "source_open_time_raw",
        "source_close_time_raw", "source_timestamp_unit", "raw_file_sha256", "ingestion_run_id"
    ]
    return pd.DataFrame(records, columns=ohlcv_columns)
