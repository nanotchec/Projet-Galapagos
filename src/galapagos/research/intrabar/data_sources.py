"""Intrabar data sources registry and schema definitions."""
from __future__ import annotations

# Registry of supported sources
SUPPORTED_SOURCES = ["binance", "bybit"]
SUPPORTED_TIMEFRAMES = ["5m", "1m"]

# Standard schema for intrabar data
INTRABAR_SCHEMA = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "source",
    "symbol",
    "timeframe",
    "available_timestamp",
    "downloaded_at",
]
