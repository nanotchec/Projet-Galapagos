from __future__ import annotations
from typing import List, Any, Dict
from .normalized_record_schema import NormalizedMicrostructureRecord
from .timestamp_normalizer import TimestampNormalizer


class FieldMapper:
    """Maps raw source fields to normalized records (V1.55)."""

    @staticmethod
    def map_binance_kline(raw: List[Any], symbol: str, timeframe: str, ingest_ts: int) -> NormalizedMicrostructureRecord:
        """
        Binance Kline format:
        [
          1499040000000,      // [0] Open time
          "0.01634790",       // [1] Open
          "0.80000000",       // [2] High
          "0.01575800",       // [3] Low
          "0.01577100",       // [4] Close
          "148976.11427815",  // [5] Volume
          1499644799999,      // [6] Close time
          "2434.19055334",    // [7] Quote asset volume
          308,                // [8] Number of trades
          "1756.87402397",    // [9] Taker buy base asset volume
          "28.46694368",      // [10] Taker buy quote asset volume
          "17928899.62484339" // [11] Ignore.
        ]
        """
        event_ts = int(raw[0])
        # Estimation for available_ts if not provided by source (using close_time [6] + 1ms)
        available_ts = int(raw[6]) + 1
        
        return NormalizedMicrostructureRecord(
            source="binance",
            symbol=symbol,
            timeframe=timeframe,
            event_ts=event_ts,
            available_ts=available_ts,
            ingest_ts=ingest_ts,
            open=float(raw[1]),
            high=float(raw[2]),
            low=float(raw[3]),
            close=float(raw[4]),
            volume=float(raw[5]),
            quote_volume=float(raw[7]),
            trade_count=int(raw[8]),
            taker_buy_base_volume=float(raw[9]),
            taker_buy_quote_volume=float(raw[10])
        )

    @staticmethod
    def map_bybit_kline(raw: List[Any], symbol: str, timeframe: str, ingest_ts: int) -> NormalizedMicrostructureRecord:
        """
        Bybit Kline format (V5):
        [
          "1633215600000",    // [0] Start time
          "47520",            // [1] Open
          "47559.5",          // [2] High
          "47520",            // [3] Low
          "47539.5",          // [4] Close
          "10.23",            // [5] Volume
          "486241.1"          // [6] Turnover (quote volume)
        ]
        Note: Bybit V5 klines in stub mode might lack taker buy volumes.
        """
        event_ts = int(raw[0])
        # Available TS estimation
        available_ts = TimestampNormalizer.estimate_available_ts(event_ts, timeframe, "bybit")

        return NormalizedMicrostructureRecord(
            source="bybit",
            symbol=symbol,
            timeframe=timeframe,
            event_ts=event_ts,
            available_ts=available_ts,
            ingest_ts=ingest_ts,
            open=float(raw[1]),
            high=float(raw[2]),
            low=float(raw[3]),
            close=float(raw[4]),
            volume=float(raw[5]),
            quote_volume=float(raw[6]),
            trade_count=0,               # Default if missing
            taker_buy_base_volume=0.0,    # Default if missing
            taker_buy_quote_volume=0.0    # Default if missing
        )
