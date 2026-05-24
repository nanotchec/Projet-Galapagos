from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from galapagos.data.public_market.quality import assess_ohlcv_quality
from galapagos.data.public_market.schemas import OHLCV_COLUMNS


TIMEFRAMES_V5_0 = ["1m", "5m", "15m", "1h"]
FORBIDDEN_OHLCV_COLUMNS_V5_0 = {
    "normalized_file_sha256",
    "future_return",
    "label",
    "target",
    "signal",
    "strategy",
    "order",
    "prediction",
    "pnl",
    "backtest",
}


def expected_rows_v5_0(total_days: int) -> dict[str, int]:
    return {"1m": total_days * 1440, "5m": total_days * 288, "15m": total_days * 96, "1h": total_days * 24}


def assess_max_history_timeframe(
    frame: pd.DataFrame,
    *,
    timeframe: str,
    expected_rows: int,
    window_start: str,
    window_end: str,
    parent_child_consistency: bool,
) -> dict[str, Any]:
    quality = assess_ohlcv_quality(frame, expected_rows=expected_rows, timeframe=timeframe).payload
    forbidden_columns = sorted(column for column in frame.columns if str(column).casefold() in FORBIDDEN_OHLCV_COLUMNS_V5_0)
    quality["parent_child_consistency"] = bool(parent_child_consistency)
    quality["forbidden_columns_present"] = forbidden_columns
    if forbidden_columns:
        quality["errors"].append(f"forbidden OHLCV columns present: {forbidden_columns}")
    if list(frame.columns) != OHLCV_COLUMNS:
        quality["errors"].append("OHLCV column schema mismatch")
    expected_min = f"{window_start}T00:00:00Z"
    expected_max = expected_max_event_ts_v5_0(window_end, timeframe)
    if quality["min_event_ts"] != expected_min:
        quality["errors"].append(f"min_event_ts {quality['min_event_ts']} != {expected_min}")
    if quality["max_event_ts"] != expected_max:
        quality["errors"].append(f"max_event_ts {quality['max_event_ts']} != {expected_max}")
    return quality


def expected_max_event_ts_v5_0(window_end: str, timeframe: str) -> str:
    base = pd.Timestamp(date.fromisoformat(window_end), tz="UTC")
    offsets = {
        "1m": pd.Timedelta(hours=23, minutes=59),
        "5m": pd.Timedelta(hours=23, minutes=55),
        "15m": pd.Timedelta(hours=23, minutes=45),
        "1h": pd.Timedelta(hours=23),
    }
    if timeframe not in offsets:
        raise ValueError("V5.0 supports timeframe=1m, 5m, 15m or 1h only.")
    return (base + offsets[timeframe]).isoformat().replace("+00:00", "Z")


def parent_child_consistent(frame_1m: pd.DataFrame, child: pd.DataFrame, timeframe: str) -> bool:
    try:
        expected = resample_max_history_ohlcv(frame_1m, target_timeframe=timeframe)
    except ValueError:
        return False
    if list(expected.columns) != list(child.columns):
        return False
    comparable_columns = [
        "source",
        "venue",
        "market_type",
        "symbol",
        "timeframe",
        "event_ts",
        "close_ts",
        "available_ts",
        "decision_ts",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "trade_count",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
        "source_open_time_raw",
        "source_close_time_raw",
        "source_timestamp_unit",
        "ingestion_run_id",
    ]
    left = expected[comparable_columns].reset_index(drop=True)
    right = child[comparable_columns].reset_index(drop=True)
    try:
        pd.testing.assert_frame_equal(left, right, check_dtype=False, atol=1e-10, rtol=1e-10)
    except AssertionError:
        return False
    return True


def resample_max_history_ohlcv(frame_1m: pd.DataFrame, *, target_timeframe: str) -> pd.DataFrame:
    if target_timeframe not in {"5m", "15m", "1h"}:
        raise ValueError("V5.0 supports target_timeframe=5m, 15m or 1h only.")
    minutes = {"5m": 5, "15m": 15, "1h": 60}[target_timeframe]
    freq = {"5m": "5min", "15m": "15min", "1h": "1h"}[target_timeframe]
    frame = frame_1m.copy()
    for column in ["event_ts", "close_ts", "available_ts", "decision_ts", "ingested_at_ts"]:
        frame[column] = pd.to_datetime(frame[column], utc=True)
    if list(frame.columns) != OHLCV_COLUMNS:
        raise ValueError("source 1m OHLCV schema mismatch")
    if not frame["event_ts"].is_monotonic_increasing:
        raise ValueError("source 1m event_ts must be physically monotonic before resampling.")
    frame["_bucket"] = frame["event_ts"].dt.floor(freq)
    bucket_sizes = frame.groupby("_bucket", sort=True).size()
    if not (bucket_sizes == minutes).all():
        raise ValueError("source 1m rows contain a partial or incomplete resampling bucket.")

    grouped = frame.groupby("_bucket", sort=True)
    result = grouped.agg(
        source=("source", "first"),
        venue=("venue", "first"),
        market_type=("market_type", "first"),
        symbol=("symbol", "first"),
        event_ts=("event_ts", "first"),
        close_ts=("close_ts", "last"),
        available_ts=("close_ts", "last"),
        decision_ts=("close_ts", "last"),
        ingested_at_ts=("ingested_at_ts", "first"),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        quote_volume=("quote_volume", "sum"),
        trade_count=("trade_count", "sum"),
        taker_buy_base_volume=("taker_buy_base_volume", "sum"),
        taker_buy_quote_volume=("taker_buy_quote_volume", "sum"),
        source_open_time_raw=("source_open_time_raw", "first"),
        source_close_time_raw=("source_close_time_raw", "last"),
        source_timestamp_unit=("source_timestamp_unit", "first"),
        raw_file_sha256=("raw_file_sha256", lambda values: ",".join(sorted(set(values.astype(str))))),
        ingestion_run_id=("ingestion_run_id", "first"),
    ).reset_index(drop=True)
    result.insert(4, "timeframe", target_timeframe)
    for column in ["trade_count", "source_open_time_raw", "source_close_time_raw"]:
        result[column] = result[column].astype("int64")
    return result[OHLCV_COLUMNS].sort_values("event_ts").reset_index(drop=True)
