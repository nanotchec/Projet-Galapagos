from __future__ import annotations


def momentum_candidate(regime: dict) -> dict:
    return {
        "strategy": "momentum",
        "enabled": regime.get("trend") in {"uptrend", "downtrend"},
        "trend": regime.get("trend"),
    }

