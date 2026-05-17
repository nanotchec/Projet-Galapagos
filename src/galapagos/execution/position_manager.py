from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Position:
    id: str
    profile: str
    asset: str
    side: str
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float | None
    max_duration_minutes: int
    strategy: str
    entry_timestamp: str
    entry_fee: float
    entry_slippage: float
    status: str = "OPEN"

    @classmethod
    def from_dict(cls, payload: dict) -> Position:
        fields = cls.__dataclass_fields__
        return cls(**{key: payload[key] for key in fields if key in payload})
