from __future__ import annotations


OHLCV_COLUMNS = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "timeframe",
    "event_ts",
    "close_ts",
    "available_ts",
    "decision_ts",
    "ingested_at_ts",
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
    "raw_file_sha256",
    "ingestion_run_id",
]

CRITICAL_COLUMNS = [
    "source",
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
    "raw_file_sha256",
    "ingestion_run_id",
]

UNIQUE_KEY_COLUMNS = ["source", "market_type", "symbol", "timeframe", "event_ts"]

NUMERIC_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
]
