"""Schemas for trade candidates and simulation results."""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import AliasChoices, BaseModel, Field, field_validator, model_validator


class TradeSide(StrEnum):
    """Side of the trade candidate."""

    LONG = "LONG"
    SHORT = "SHORT"
    WAIT = "WAIT"


class TradeCandidate(BaseModel):
    """A research-only trade candidate produced from a signal and a policy."""

    candidate_id: str
    signal_time: datetime = Field(validation_alias=AliasChoices("signal_time", "timestamp"))
    entry_time: datetime | None = None
    asset: str = "BTC"
    symbol: str = "BTCUSDT"
    timeframe: str = "4h"
    side: TradeSide
    entry_price: float = Field(gt=0)
    stop_loss: float | None = None
    take_profit: float | None = None
    max_holding_bars: int = Field(gt=0)
    max_holding_time: datetime
    source: str
    source_version: str
    signal_score: float | None = None
    confidence: float | None = None
    policy_name: str
    policy_version: str
    policy_parameters: dict[str, Any] = Field(default_factory=dict)
    data_availability: dict[str, bool] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    research_only: bool = Field(default=True)

    @property
    def timestamp(self) -> datetime:
        """Alias for signal_time for backward compatibility."""
        return self.signal_time

    @field_validator("research_only")
    @classmethod
    def validate_research_only(cls, v: bool) -> bool:
        """Ensure the candidate is strictly for research."""
        if v is not True:
            raise ValueError("TradeCandidate must be research_only")
        return v

    @model_validator(mode="after")
    def validate_times(self) -> TradeCandidate:
        """Validate temporal consistency."""
        if self.entry_time is None:
            self.entry_time = self.signal_time
        if self.entry_time < self.signal_time:
            msg = f"entry_time {self.entry_time} must be >= signal_time {self.signal_time}"
            raise ValueError(msg)
        if self.max_holding_time < self.entry_time:
            raise ValueError(
                f"max_holding_time {self.max_holding_time} must be > entry_time {self.entry_time}"
            )
        return self

    @model_validator(mode="after")
    def validate_trade_parameters(self) -> TradeCandidate:
        """Validate SL/TP consistency with side."""
        if self.side == TradeSide.LONG:
            if self.stop_loss is not None and self.stop_loss >= self.entry_price:
                raise ValueError(
                    f"LONG stop_loss {self.stop_loss} must be < entry_price {self.entry_price}"
                )
            if self.take_profit is not None and self.take_profit <= self.entry_price:
                raise ValueError(
                    f"LONG take_profit {self.take_profit} must be > entry_price {self.entry_price}"
                )
        elif self.side == TradeSide.SHORT:
            if self.stop_loss is not None and self.stop_loss <= self.entry_price:
                raise ValueError(
                    f"SHORT stop_loss {self.stop_loss} must be > entry_price {self.entry_price}"
                )
            if self.take_profit is not None and self.take_profit >= self.entry_price:
                raise ValueError(
                    f"SHORT take_profit {self.take_profit} must be < entry_price {self.entry_price}"
                )
        return self


class TradeSimulationResult(BaseModel):
    """Result of an intrabar simulation for a TradeCandidate."""

    candidate_id: str
    signal_time: datetime
    entry_time: datetime
    side: TradeSide
    entry_price: float
    exit_price: float | None = None
    exit_time: datetime | None = None
    exit_reason: str | None = None
    pnl_abs: float = 0.0
    pnl_pct: float = 0.0
    cost_proxy_abs: float = 0.0
    cost_proxy_pct: float = 0.0
    pnl_after_cost_abs: float = 0.0
    pnl_after_cost_pct: float = 0.0
    mfe_pct: float = 0.0
    mae_pct: float = 0.0
    bars_held_intrabar: int = 0
    used_intrabar: bool = False
    used_fallback: bool = False
    ambiguous: bool = False
    coverage_pct: float = 0.0
    simulation_status: str
    notes: str = ""
