from __future__ import annotations


def no_trade_scenario(reason: str) -> dict:
    return {"strategy": "no_trade", "bias": "flat", "reason": reason}

