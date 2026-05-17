from __future__ import annotations


def mean_reversion_candidate(regime: dict) -> dict:
    return {
        "strategy": "mean_reversion",
        "enabled": regime.get("trend") in {"range", "unknown"},
        "notes": "Requires controlled volatility and clear invalidation.",
    }

