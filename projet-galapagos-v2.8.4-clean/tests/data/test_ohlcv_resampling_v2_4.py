from __future__ import annotations

import pandas as pd
import pytest

from galapagos.data.public_market.resampling import resample_ohlcv
from galapagos.data.public_market.schemas import OHLCV_COLUMNS


def test_resample_5m_row_count_and_aggregation() -> None:
    frame = _frame_1m(1440)
    result = resample_ohlcv(frame, target_timeframe="5m")
    first = result.iloc[0]
    assert len(result) == 288
    assert first["timeframe"] == "5m"
    assert first["open"] == pytest.approx(frame.iloc[0]["open"])
    assert first["high"] == pytest.approx(frame.iloc[:5]["high"].max())
    assert first["low"] == pytest.approx(frame.iloc[:5]["low"].min())
    assert first["close"] == pytest.approx(frame.iloc[4]["close"])
    assert first["volume"] == pytest.approx(frame.iloc[:5]["volume"].sum())
    assert first["quote_volume"] == pytest.approx(frame.iloc[:5]["quote_volume"].sum())
    assert first["trade_count"] == int(frame.iloc[:5]["trade_count"].sum())
    assert first["source_open_time_raw"] == frame.iloc[0]["source_open_time_raw"]
    assert first["source_close_time_raw"] == frame.iloc[4]["source_close_time_raw"]


def test_resample_15m_row_count_and_aggregation() -> None:
    frame = _frame_1m(1440)
    result = resample_ohlcv(frame, target_timeframe="15m")
    first = result.iloc[0]
    assert len(result) == 96
    assert first["timeframe"] == "15m"
    assert first["high"] == pytest.approx(frame.iloc[:15]["high"].max())
    assert first["volume"] == pytest.approx(frame.iloc[:15]["volume"].sum())
    assert first["close_ts"] == frame.iloc[14]["close_ts"]


def test_resample_1h_row_count_and_aggregation() -> None:
    frame = _frame_1m(1440)
    result = resample_ohlcv(frame, target_timeframe="1h")
    first = result.iloc[0]
    assert len(result) == 24
    assert first["timeframe"] == "1h"
    assert first["low"] == pytest.approx(frame.iloc[:60]["low"].min())
    assert first["taker_buy_quote_volume"] == pytest.approx(frame.iloc[:60]["taker_buy_quote_volume"].sum())
    assert first["close"] == pytest.approx(frame.iloc[59]["close"])


def test_resample_preserves_utc_timestamps() -> None:
    result = resample_ohlcv(_frame_1m(1440), target_timeframe="5m")
    for column in ["event_ts", "close_ts", "available_ts", "decision_ts", "ingested_at_ts"]:
        series = pd.to_datetime(result[column], utc=True)
        assert str(series.dt.tz) == "UTC"


def test_resample_rejects_unsupported_timeframe() -> None:
    with pytest.raises(ValueError, match="5m, 15m or 1h"):
        resample_ohlcv(_frame_1m(1440), target_timeframe="30m")


def test_resample_rejects_partial_bucket_or_missing_1m_rows() -> None:
    frame = _frame_1m(1439)
    with pytest.raises(ValueError, match="partial or incomplete"):
        resample_ohlcv(frame, target_timeframe="5m")


def test_resample_physical_order_is_monotonic() -> None:
    result = resample_ohlcv(_frame_1m(1440), target_timeframe="5m")
    assert result["event_ts"].is_monotonic_increasing
    shuffled = _frame_1m(1440).iloc[[0, 2, 1, *range(3, 1440)]].reset_index(drop=True)
    with pytest.raises(ValueError, match="physically monotonic"):
        resample_ohlcv(shuffled, target_timeframe="5m")


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
    return pd.DataFrame(records, columns=OHLCV_COLUMNS)
