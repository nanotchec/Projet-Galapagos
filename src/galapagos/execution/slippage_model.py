from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlippageModel:
    slippage_bps: float = 5.0

    def apply(self, price: float, side: str, action: str) -> tuple[float, float]:
        rate = self.slippage_bps / 10_000
        direction = 1 if action == "entry" else -1
        if side == "SHORT":
            direction *= -1
        adjusted = price * (1 + direction * rate)
        return adjusted, abs(adjusted - price)

