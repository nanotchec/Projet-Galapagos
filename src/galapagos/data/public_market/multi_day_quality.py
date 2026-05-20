from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.data.public_market.quality import assess_ohlcv_quality
from galapagos.data.public_market.schemas import OHLCV_COLUMNS


EXPECTED_ROWS_V2_9 = {"1m": 10080, "5m": 2016, "15m": 672, "1h": 168}
EXPECTED_MAX_EVENT_TS_V2_9 = {
    "1m": "2024-01-21T23:59:00Z",
    "5m": "2024-01-21T23:55:00Z",
    "15m": "2024-01-21T23:45:00Z",
    "1h": "2024-01-21T23:00:00Z",
}
EXPECTED_MIN_EVENT_TS_V2_9 = "2024-01-15T00:00:00Z"
FORBIDDEN_OHLCV_COLUMNS_V2_9 = {
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


def assess_multi_day_timeframe(
    frame: pd.DataFrame,
    *,
    timeframe: str,
    parent_child_consistency: bool,
) -> dict[str, Any]:
    quality = assess_ohlcv_quality(
        frame,
        expected_rows=EXPECTED_ROWS_V2_9[timeframe],
        timeframe=timeframe,
    ).payload
    forbidden_columns = sorted(column for column in frame.columns if str(column).casefold() in FORBIDDEN_OHLCV_COLUMNS_V2_9)
    quality["parent_child_consistency"] = bool(parent_child_consistency)
    quality["forbidden_columns_present"] = forbidden_columns
    if forbidden_columns:
        quality["errors"].append(f"forbidden OHLCV columns present: {forbidden_columns}")
    if list(frame.columns) != OHLCV_COLUMNS:
        quality["errors"].append("OHLCV column schema mismatch")
    if quality["min_event_ts"] != EXPECTED_MIN_EVENT_TS_V2_9:
        quality["errors"].append(f"min_event_ts {quality['min_event_ts']} != {EXPECTED_MIN_EVENT_TS_V2_9}")
    if quality["max_event_ts"] != EXPECTED_MAX_EVENT_TS_V2_9[timeframe]:
        quality["errors"].append(
            f"max_event_ts {quality['max_event_ts']} != {EXPECTED_MAX_EVENT_TS_V2_9[timeframe]}"
        )
    return quality


def parent_child_consistent(frame_1m: pd.DataFrame, child: pd.DataFrame, timeframe: str) -> bool:
    try:
        expected = resample_multi_day_ohlcv(frame_1m, target_timeframe=timeframe)
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


def resample_multi_day_ohlcv(frame_1m: pd.DataFrame, *, target_timeframe: str) -> pd.DataFrame:
    if target_timeframe not in {"5m", "15m", "1h"}:
        raise ValueError("V2.9 supports target_timeframe=5m, 15m or 1h only.")
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
    rows: list[dict[str, Any]] = []
    for _bucket, group in frame.groupby("_bucket", sort=True):
        group = group.sort_values("event_ts").reset_index(drop=True)
        first = group.iloc[0]
        last = group.iloc[-1]
        rows.append(
            {
                "source": first["source"],
                "venue": first["venue"],
                "market_type": first["market_type"],
                "symbol": first["symbol"],
                "timeframe": target_timeframe,
                "event_ts": first["event_ts"],
                "close_ts": last["close_ts"],
                "available_ts": last["close_ts"],
                "decision_ts": last["close_ts"],
                "ingested_at_ts": first["ingested_at_ts"],
                "open": float(first["open"]),
                "high": float(group["high"].max()),
                "low": float(group["low"].min()),
                "close": float(last["close"]),
                "volume": float(group["volume"].sum()),
                "quote_volume": float(group["quote_volume"].sum()),
                "trade_count": int(group["trade_count"].sum()),
                "taker_buy_base_volume": float(group["taker_buy_base_volume"].sum()),
                "taker_buy_quote_volume": float(group["taker_buy_quote_volume"].sum()),
                "source_open_time_raw": int(first["source_open_time_raw"]),
                "source_close_time_raw": int(last["source_close_time_raw"]),
                "source_timestamp_unit": first["source_timestamp_unit"],
                "raw_file_sha256": ",".join(sorted(set(group["raw_file_sha256"].astype(str)))),
                "ingestion_run_id": first["ingestion_run_id"],
            }
        )
    result = pd.DataFrame(rows, columns=OHLCV_COLUMNS).sort_values("event_ts").reset_index(drop=True)
    expected_rows = EXPECTED_ROWS_V2_9[target_timeframe]
    if len(result) != expected_rows:
        raise ValueError(f"resampled {target_timeframe} rows {len(result)} != expected {expected_rows}")
    return result
