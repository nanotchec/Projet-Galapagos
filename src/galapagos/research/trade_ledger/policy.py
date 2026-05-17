"""Deterministic trade policies for research evaluation."""
from __future__ import annotations

from typing import Any


def fixed_percent_policy(entry_price: float, side: str) -> dict[str, Any]:
    """Apply fixed percentage SL/TP (1.5% SL, 3% TP)."""
    if side == "LONG":
        return {
            "stop_loss": entry_price * 0.985,
            "take_profit": entry_price * 1.03,
            "max_holding_bars": 6,
        }
    elif side == "SHORT":
        return {
            "stop_loss": entry_price * 1.015,
            "take_profit": entry_price * 0.97,
            "max_holding_bars": 6,
        }
    return {"stop_loss": None, "take_profit": None, "max_holding_bars": 6}


def atr_proxy_policy(
    entry_price: float, side: str, atr_pct: float, stop_mult: float = 1.5, tp_mult: float = 2.0
) -> dict[str, Any]:
    """Apply ATR-based SL/TP with conservative caps."""
    # stop_dist as percentage of entry price
    stop_dist = stop_mult * atr_pct
    tp_dist = tp_mult * stop_dist

    # Caps (0.5% min SL, 5% max SL, 10% max TP)
    stop_dist = max(0.005, min(0.05, stop_dist))
    tp_dist = min(0.10, tp_dist)

    if side == "LONG":
        return {
            "stop_loss": entry_price * (1 - stop_dist),
            "take_profit": entry_price * (1 + tp_dist),
            "max_holding_bars": 6,
        }
    elif side == "SHORT":
        return {
            "stop_loss": entry_price * (1 + stop_dist),
            "take_profit": entry_price * (1 - tp_dist),
            "max_holding_bars": 6,
        }
    return {"stop_loss": None, "take_profit": None, "max_holding_bars": 6}


def horizon_only_policy(entry_price: float, side: str, bars: int = 6) -> dict[str, Any]:
    """Exit only by maximum holding time (no SL/TP)."""
    return {"stop_loss": None, "take_profit": None, "max_holding_bars": bars}
