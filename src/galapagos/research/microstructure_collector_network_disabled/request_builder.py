from __future__ import annotations
from typing import List, Optional
from .config_schema import CollectorConfig, RequestPlan
from .binance_adapter_stub import BinanceAdapterStub
from .bybit_adapter_stub import BybitAdapterStub


class RequestBuilder:
    """Orchestrates the construction of request plans."""

    def __init__(self, config: CollectorConfig):
        self.config = config
        self.adapter = self._get_adapter()

    def _get_adapter(self):
        if self.config.source == "binance":
            return BinanceAdapterStub(self.config)
        elif self.config.source == "bybit":
            return BybitAdapterStub(self.config)
        else:
            raise ValueError(f"Unsupported source: {self.config.source}")

    def build_plan(self) -> RequestPlan:
        """Builds a complete request plan."""
        requests = self.adapter.build_requests()
        
        # Limit the number of requests for safety in V1.54
        if len(requests) > self.config.max_requests:
             requests = requests[:self.config.max_requests]
             
        # Theoretical estimation
        candle_ms = 60 * 1000
        if self.config.timeframe == "5m":
            candle_ms = 5 * 60 * 1000
        
        total_rows = (self.config.end_ts - self.config.start_ts) // candle_ms
        
        return RequestPlan(
            config=self.config,
            requests=requests,
            total_expected_rows=total_rows,
            estimated_files_count=len(requests)
        )
