from __future__ import annotations


def breakout_candidate(indicators: dict, regime: dict) -> dict:
    return {
        "strategy": "breakout",
        "enabled": regime.get("volatility_regime") in {"normal", "high"},
        "notes": "Requires close confirmation, above-average volume, and non-extreme funding.",
        "last_close": indicators.get("last_close"),
    }

