from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

from galapagos.features.ohlcv_aggtrades_5y_feature_store_validation_v9_38 import (
    build_aggtrades_limitations_v9_38,
    validate_feature_frame_v9_38,
    validate_rolling_features_v9_38,
)
from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_37_schemas import (
    AGGTRADES_SOURCE_TYPE,
    FEATURE_SCHEMA_VERSION,
    FORBIDDEN_FEATURE_COLUMNS,
    OHLCV_SOURCE_TYPE,
    SOURCE_AGGTRADES_VALIDATION_VERSION,
    SOURCE_OHLCV_VALIDATION_VERSION,
    STRICT_COLUMNS,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
)


def test_v9_38_validation_keeps_v9_37_strict_schema() -> None:
    frame = _sample_feature_frame(rows=90)

    result = validate_feature_frame_v9_38(frame, timeframe="1m", path=Path("features.parquet"))

    assert list(frame.columns) == STRICT_COLUMNS
    assert set(frame.columns).isdisjoint(FORBIDDEN_FEATURE_COLUMNS)
    assert result["strict_schema_status"] == "PASS"
    assert result["feature_available_ts_lte_decision_ts"] is True
    assert result["available_ts_lte_decision_ts"] is True
    assert result["quality_status"] == "FAIL"
    assert any("actual_rows_mismatch" in error for error in result["errors"])


def test_v9_38_detects_rolling_feature_mismatch() -> None:
    frame = _sample_feature_frame(rows=90)
    frame.loc[20, "volume_rolling_mean_5"] = 999999.0

    errors = validate_rolling_features_v9_38(frame)

    assert any("volume_rolling_mean_5_rolling_mismatch" in error for error in errors)


def test_v9_38_detects_leakage_timestamp_violation() -> None:
    frame = _sample_feature_frame(rows=90)
    frame.loc[0, "feature_available_ts"] = frame.loc[0, "decision_ts"] + pd.Timedelta(seconds=1)

    result = validate_feature_frame_v9_38(frame, timeframe="1m", path=Path("features.parquet"))

    assert result["feature_available_ts_lte_decision_ts"] is False
    assert any("feature_available_ts_after_decision_ts" in error for error in result["errors"])


def test_v9_38_zero_trade_flags_are_validated() -> None:
    frame = _sample_feature_frame(rows=90, zero_trade_index=10)

    result = validate_feature_frame_v9_38(frame, timeframe="1m", path=Path("features.parquet"))

    assert result["zero_trade_bucket_summary"]["zero_trade_rows"] == 1
    assert result["zero_trade_bucket_summary"]["rolling_count_coherent"] is True
    assert result["zero_trade_bucket_summary"]["zero_trade_bucket_blocking"] is False


def test_v9_38_classifies_direct_aggtrades_limitations_as_non_blocking() -> None:
    limitations = build_aggtrades_limitations_v9_38()

    assert limitations["direct_aggtrades_full_scan_performed"] is False
    assert limitations["non_blocking_for_current_feature_store_validation"] is True
    assert limitations["blocking_for_next_dataset"] is False


def test_v9_38_tests_do_not_use_placeholder_bodies() -> None:
    source = Path(__file__).read_text(encoding="utf-8")

    assert "pass\n" not in source
    assert ("assert " + "True") not in source


def _sample_feature_frame(rows: int, zero_trade_index: int | None = None) -> pd.DataFrame:
    open_ts = pd.date_range("2021-05-05T00:00:00Z", periods=rows, freq="min")
    close_ts = open_ts + pd.Timedelta(minutes=1) - pd.Timedelta(milliseconds=1)
    close = pd.Series([100.0 + index * 0.1 for index in range(rows)])
    volume = pd.Series([10.0] * rows)
    quote_volume = pd.Series([1000.0] * rows)
    trades_count = pd.Series([5] * rows)
    taker_buy = pd.Series([4.0] * rows)
    if zero_trade_index is not None:
        volume.loc[zero_trade_index] = 0.0
        quote_volume.loc[zero_trade_index] = 0.0
        trades_count.loc[zero_trade_index] = 0
        taker_buy.loc[zero_trade_index] = 0.0
    taker_sell = volume - taker_buy
    imbalance = pd.Series([0.0 if vol == 0 else (buy - sell) / vol for buy, sell, vol in zip(taker_buy, taker_sell, volume, strict=True)])
    close_return = (close + 0.5).pct_change()
    frame = pd.DataFrame(
        {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "event_ts": open_ts,
            "open_ts": open_ts,
            "close_ts": close_ts,
            "decision_ts": close_ts,
            "available_ts": close_ts,
            "feature_available_ts": close_ts,
            "feature_run_id": "test_run",
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "ohlcv_source_type": OHLCV_SOURCE_TYPE,
            "aggtrades_source_type": AGGTRADES_SOURCE_TYPE,
            "source_ohlcv_validation_version": SOURCE_OHLCV_VALIDATION_VERSION,
            "source_aggtrades_validation_version": SOURCE_AGGTRADES_VALIDATION_VERSION,
            "source_window_start": TARGET_WINDOW_START,
            "source_window_end": TARGET_WINDOW_END,
            "close_return_1": close_return,
            "log_return_1": np.log((close + 0.5) / (close + 0.5).shift(1)),
            "rolling_return_5": (close + 0.5) / (close + 0.5).shift(5) - 1.0,
            "rolling_return_15": (close + 0.5) / (close + 0.5).shift(15) - 1.0,
            "rolling_return_60": (close + 0.5) / (close + 0.5).shift(60) - 1.0,
            "rolling_volatility_5": close_return.rolling(5, min_periods=5).std(),
            "rolling_volatility_15": close_return.rolling(15, min_periods=15).std(),
            "rolling_volatility_60": close_return.rolling(60, min_periods=60).std(),
            "high_low_range": 2.0 / (close + 0.5),
            "close_open_return": (close + 0.5) / close - 1.0,
            "candle_body": 0.5 / (close + 0.5),
            "upper_wick": 0.5 / (close + 0.5),
            "lower_wick": 1.0 / (close + 0.5),
            "volume": volume,
            "quote_volume": quote_volume,
            "trades_count": trades_count,
            "volume_rolling_mean_5": volume.rolling(5, min_periods=5).mean(),
            "volume_rolling_mean_15": volume.rolling(15, min_periods=15).mean(),
            "volume_rolling_mean_60": volume.rolling(60, min_periods=60).mean(),
            "volume_rolling_std_5": volume.rolling(5, min_periods=5).std(),
            "volume_rolling_std_15": volume.rolling(15, min_periods=15).std(),
            "volume_rolling_std_60": volume.rolling(60, min_periods=60).std(),
            "zero_trade_bucket_rolling_count_60": (trades_count == 0).astype("int64").rolling(60, min_periods=1).sum(),
            "agg_trade_count": trades_count,
            "agg_trade_volume": volume,
            "agg_trade_quote_volume": quote_volume,
            "average_trade_size": [0.0 if count == 0 else vol / count for vol, count in zip(volume, trades_count, strict=True)],
            "taker_buy_base_volume": taker_buy,
            "taker_sell_base_volume": taker_sell,
            "taker_buy_ratio": [0.0 if vol == 0 else buy / vol for buy, vol in zip(taker_buy, volume, strict=True)],
            "taker_buy_sell_imbalance": imbalance,
            "trade_intensity_rolling_5": trades_count.rolling(5, min_periods=5).mean(),
            "trade_intensity_rolling_15": trades_count.rolling(15, min_periods=15).mean(),
            "trade_intensity_rolling_60": trades_count.rolling(60, min_periods=60).mean(),
            "agg_trade_volume_rolling_mean_5": volume.rolling(5, min_periods=5).mean(),
            "agg_trade_volume_rolling_mean_15": volume.rolling(15, min_periods=15).mean(),
            "agg_trade_volume_rolling_mean_60": volume.rolling(60, min_periods=60).mean(),
            "taker_imbalance_rolling_mean_5": imbalance.rolling(5, min_periods=5).mean(),
            "taker_imbalance_rolling_mean_15": imbalance.rolling(15, min_periods=15).mean(),
            "taker_imbalance_rolling_mean_60": imbalance.rolling(60, min_periods=60).mean(),
            "missing_aggtrades_flag": (trades_count == 0).astype("int64"),
            "warmup_row": False,
            "zero_trade_bucket": trades_count == 0,
            "feature_null_count": 0,
            "feature_error_count": 0,
            "row_valid_for_features": True,
            "feature_invalid_reason": "",
        }
    )
    feature_columns = [column for column in STRICT_COLUMNS if column not in {"source", "venue", "market_type", "symbol", "timeframe", "event_ts", "open_ts", "close_ts", "decision_ts", "available_ts", "feature_available_ts", "feature_run_id", "feature_schema_version", "ohlcv_source_type", "aggtrades_source_type", "source_ohlcv_validation_version", "source_aggtrades_validation_version", "source_window_start", "source_window_end", "warmup_row", "zero_trade_bucket", "feature_null_count", "feature_error_count", "row_valid_for_features", "feature_invalid_reason"}]
    frame["feature_null_count"] = frame[feature_columns].isna().sum(axis=1).astype("int64")
    frame["warmup_row"] = frame["feature_null_count"] > 0
    return frame[STRICT_COLUMNS]
