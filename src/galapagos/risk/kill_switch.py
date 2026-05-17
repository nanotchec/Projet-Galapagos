from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KillSwitchResult:
    active: bool
    reasons: list[str]


class KillSwitch:
    def evaluate(
        self,
        *,
        enabled: bool,
        data_available: bool,
        daily_loss_fraction: float,
        weekly_loss_fraction: float,
        max_daily_loss: float,
        max_weekly_loss: float,
        volatility_regime: str | None = None,
    ) -> KillSwitchResult:
        if not enabled:
            return KillSwitchResult(active=False, reasons=[])
        reasons: list[str] = []
        if not data_available:
            reasons.append("Required data unavailable")
        if daily_loss_fraction <= -abs(max_daily_loss):
            reasons.append("Daily loss limit reached")
        if weekly_loss_fraction <= -abs(max_weekly_loss):
            reasons.append("Weekly loss limit reached")
        if volatility_regime == "extreme":
            reasons.append("Extreme volatility regime")
        return KillSwitchResult(active=bool(reasons), reasons=reasons)

