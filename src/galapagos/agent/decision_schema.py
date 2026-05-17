from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class DecisionType(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"
    CLOSE = "CLOSE"
    HOLD = "HOLD"
    NO_TRADE = "NO_TRADE"


class StrategyType(StrEnum):
    NO_TRADE = "no_trade"
    BREAKOUT = "breakout"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    DERIVATIVES_SIGNAL = "derivatives_signal"
    VOLATILITY_REGIME = "volatility_regime"
    RISK_REDUCTION = "risk_reduction"
    CLOSE_POSITION = "close_position"


class AgentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    decision: DecisionType
    profile: str
    asset: str
    strategy: StrategyType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_summary: str = Field(min_length=1)
    horizon: str
    reference_entry_price: float | None = Field(default=None, gt=0)
    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
    risk_fraction: float = Field(ge=0.0, le=1.0)
    max_duration_minutes: int = Field(ge=0)
    invalidation_conditions: list[str]
    critical_data_used: list[str]
    setup_quality: str = Field(default="poor", pattern="^(poor|acceptable|good|excellent)$")
    setup_quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    why_not_no_trade: str | None = None

    @model_validator(mode="after")
    def validate_trade_fields(self) -> AgentDecision:
        if self.decision in {DecisionType.LONG, DecisionType.SHORT}:
            if self.reference_entry_price is None:
                raise ValueError("LONG/SHORT requires reference_entry_price")
            if self.stop_loss is None:
                raise ValueError("LONG/SHORT requires stop_loss")
            if self.take_profit is None and self.max_duration_minutes <= 0:
                raise ValueError("LONG/SHORT requires take_profit or max_duration_minutes")
            if self.risk_fraction <= 0:
                raise ValueError("LONG/SHORT requires positive risk_fraction")
        if self.decision == DecisionType.NO_TRADE and self.risk_fraction != 0:
            raise ValueError("NO_TRADE risk_fraction must be 0")
        return self


def no_trade_decision(
    profile: str = "unknown",
    asset: str = "unknown",
    horizon: str = "unknown",
    reason: str = "Invalid or unavailable decision.",
) -> AgentDecision:
    return AgentDecision(
        decision=DecisionType.NO_TRADE,
        profile=profile,
        asset=asset,
        strategy=StrategyType.NO_TRADE,
        confidence=0.0,
        reasoning_summary=reason,
        horizon=horizon,
        reference_entry_price=None,
        stop_loss=None,
        take_profit=None,
        risk_fraction=0.0,
        max_duration_minutes=0,
        invalidation_conditions=[],
        critical_data_used=[],
    )


def parse_agent_decision(payload: Any, profile: str, asset: str, horizon: str) -> AgentDecision:
    try:
        if isinstance(payload, str):
            return AgentDecision.model_validate_json(payload)
        return AgentDecision.model_validate(payload)
    except (ValidationError, ValueError, TypeError) as exc:
        return no_trade_decision(profile, asset, horizon, f"Invalid LLM decision: {exc}")
