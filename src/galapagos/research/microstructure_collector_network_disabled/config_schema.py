from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional


class CollectorConfig(BaseModel):
    """Schema for the microstructure collector configuration."""
    version: str = Field(..., description="Project version (e.g., V1.54)")
    source: str = Field(..., description="Data source name (e.g., binance, bybit)")
    symbol: str = Field(..., description="Trading pair (e.g., BTCUSDT)")
    timeframe: str = Field(..., description="Data resolution (e.g., 1m, 5m)")
    start_ts: int = Field(..., description="Start timestamp (ms)")
    end_ts: int = Field(..., description="End timestamp (ms)")
    dry_run_only: bool = Field(True, description="Enforce dry-run mode")
    network_disabled: bool = Field(True, description="Explicitly disable network access")
    max_requests: int = Field(100, description="Maximum number of requests allowed in plan")


class RequestPlan(BaseModel):
    """Represents a set of theoretical requests to be executed."""
    config: CollectorConfig
    requests: List[dict]
    total_expected_rows: int
    estimated_files_count: int
