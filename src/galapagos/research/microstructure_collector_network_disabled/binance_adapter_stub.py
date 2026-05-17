from __future__ import annotations
from typing import List
from .source_adapter_base import SourceAdapter


class BinanceAdapterStub(SourceAdapter):
    """Stub for Binance source adapter (V1.54)."""

    def build_requests(self) -> List[dict]:
        """Build theoretical Binance kline requests."""
        requests = []
        # Simulate building requests by chunking the time range
        # (e.g., 1000 candles per request)
        duration_ms = self.config.end_ts - self.config.start_ts
        candle_ms = 60 * 1000  # 1m default for stub logic
        if self.config.timeframe == "5m":
            candle_ms = 5 * 60 * 1000
            
        chunk_size = 1000 * candle_ms
        current_start = self.config.start_ts
        
        while current_start < self.config.end_ts:
            current_end = min(current_start + chunk_size, self.config.end_ts)
            requests.append({
                "source": "binance",
                "method": "GET",
                "endpoint": "/api/v3/klines",
                "params": {
                    "symbol": self.config.symbol,
                    "interval": self.config.timeframe,
                    "startTime": current_start,
                    "endTime": current_end,
                    "limit": 1000
                }
            })
            current_start = current_end + 1
            
        return requests

    def validate_request(self, request: dict) -> bool:
        """Simple validation for the stub."""
        return request.get("source") == "binance" and "params" in request
