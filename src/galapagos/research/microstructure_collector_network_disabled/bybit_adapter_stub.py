from __future__ import annotations
from typing import List
from .source_adapter_base import SourceAdapter


class BybitAdapterStub(SourceAdapter):
    """Stub for Bybit source adapter (V1.54)."""

    def build_requests(self) -> List[dict]:
        """Build theoretical Bybit kline requests."""
        requests = []
        # Similar logic to Binance but with Bybit specific parameters
        duration_ms = self.config.end_ts - self.config.start_ts
        candle_ms = 60 * 1000
        if self.config.timeframe == "5m":
            candle_ms = 5 * 60 * 1000
            
        chunk_size = 200 * candle_ms # Bybit limit is often 200
        current_start = self.config.start_ts
        
        while current_start < self.config.end_ts:
            current_end = min(current_start + chunk_size, self.config.end_ts)
            requests.append({
                "source": "bybit",
                "method": "GET",
                "endpoint": "/v5/market/kline",
                "params": {
                    "category": "spot",
                    "symbol": self.config.symbol,
                    "interval": "5" if self.config.timeframe == "5m" else "1",
                    "start": current_start,
                    "end": current_end,
                    "limit": 200
                }
            })
            current_start = current_end + 1
            
        return requests

    def validate_request(self, request: dict) -> bool:
        """Simple validation for the stub."""
        return request.get("source") == "bybit" and "params" in request
