from __future__ import annotations


class TimestampNormalizer:
    """Normalizes and validates timestamps for causality compliance (V1.55)."""

    @staticmethod
    def validate_causality(event_ts: int, available_ts: int, ingest_ts: int) -> bool:
        """
        Enforce: event_ts <= available_ts <= ingest_ts.
        This ensures no lookahead or reverse causality.
        """
        return event_ts <= available_ts <= ingest_ts

    @staticmethod
    def normalize_to_utc(ts: int) -> int:
        """Ensures timestamp is in UTC (identity for unix ms)."""
        # In our system, all timestamps are already expected to be Unix ms UTC.
        return ts

    @staticmethod
    def estimate_available_ts(event_ts: int, timeframe: str, source: str) -> int:
        """
        Estimate when a kline becomes available based on timeframe.
        Rule: closing_time = event_ts + timeframe_duration.
        Available should be >= closing_time.
        """
        ms_map = {
            "1m": 60 * 1000,
            "5m": 5 * 60 * 1000,
            "1h": 60 * 60 * 1000
        }
        duration = ms_map.get(timeframe, 0)
        # We assume availability is slightly after the close (e.g. +10ms for network/processing latency)
        return event_ts + duration + 10
