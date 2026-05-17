from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeeModel:
    fee_rate: float = 0.001

    def calculate(self, notional: float) -> float:
        return abs(notional) * self.fee_rate

