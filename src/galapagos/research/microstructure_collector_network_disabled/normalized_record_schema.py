from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


class NormalizedMicrostructureRecord(BaseModel):
    """Schema for a single normalized microstructure record (V1.55)."""
    
    source: str = Field(..., description="Data source (e.g., binance, bybit)")
    symbol: str = Field(..., description="Trading pair symbol")
    timeframe: str = Field(..., description="Data timeframe (e.g., 1m, 5m)")
    
    # Causality Timestamps
    event_ts: int = Field(..., description="Timestamp of the event (opening of kline)")
    available_ts: int = Field(..., description="Timestamp when the data became available to the public")
    ingest_ts: int = Field(..., description="Timestamp of ingestion into the local system")
    
    # Core OHLCV
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: float = Field(..., description="Base asset volume")
    
    # Extended Microstructure
    quote_volume: float = Field(..., description="Quote asset volume")
    trade_count: int = Field(..., description="Number of trades")
    taker_buy_base_volume: float = Field(..., description="Taker buy base asset volume")
    taker_buy_quote_volume: float = Field(..., description="Taker buy quote asset volume")
    
    # Optional fields for future refinement
    extra_metadata: Optional[dict] = Field(default_factory=dict, description="Additional source-specific metadata")
