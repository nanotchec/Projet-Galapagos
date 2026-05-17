"""Simulate exits (TP/SL) using intrabar data."""
from __future__ import annotations

from typing import Any

import pandas as pd


def simulate_intrabar_exit(
    side: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    entry_time: pd.Timestamp,
    max_exit_time: pd.Timestamp,
    intrabar_slice: pd.DataFrame,
    fallback_policy: str = "conservative",
) -> dict[str, Any]:
    """Simulate realistic exit using intrabar data."""
    if intrabar_slice.empty:
        # Fallback No Intrabar
        return {
            "exit_reason": "fallback_no_intrabar",
            "exit_price": 0.0,  # Handled by higher level logic based on 4h candle
            "exit_time": max_exit_time,
            "bars_held_intrabar": 0,
            "ambiguous": False,
            "used_fallback": True,
        }

    bars_held = 0

    for _, row in intrabar_slice.iterrows():
        bars_held += 1
        high = row["high"]
        low = row["low"]
        ts = row["timestamp"]

        tp_hit = False
        sl_hit = False

        if side == "LONG":
            tp_hit = high >= take_profit
            sl_hit = low <= stop_loss
        else:  # SHORT
            tp_hit = low <= take_profit
            sl_hit = high >= stop_loss

        if tp_hit and sl_hit:
            # Ambiguous inside the same intrabar candle
            if fallback_policy == "conservative":
                return {
                    "exit_reason": "stop_loss",
                    "exit_price": stop_loss,
                    "exit_time": ts,
                    "bars_held_intrabar": bars_held,
                    "ambiguous": True,
                    "used_fallback": False,
                }
            elif fallback_policy == "optimistic":
                return {
                    "exit_reason": "take_profit",
                    "exit_price": take_profit,
                    "exit_time": ts,
                    "bars_held_intrabar": bars_held,
                    "ambiguous": True,
                    "used_fallback": False,
                }
            else:
                return {
                    "exit_reason": "ambiguous",
                    "exit_price": stop_loss,  # default safely
                    "exit_time": ts,
                    "bars_held_intrabar": bars_held,
                    "ambiguous": True,
                    "used_fallback": False,
                }

        elif tp_hit:
            return {
                "exit_reason": "take_profit",
                "exit_price": take_profit,
                "exit_time": ts,
                "bars_held_intrabar": bars_held,
                "ambiguous": False,
                "used_fallback": False,
            }
        elif sl_hit:
            return {
                "exit_reason": "stop_loss",
                "exit_price": stop_loss,
                "exit_time": ts,
                "bars_held_intrabar": bars_held,
                "ambiguous": False,
                "used_fallback": False,
            }

    # Timeout / End of slice reached without hitting TP or SL
    last_row = intrabar_slice.iloc[-1]
    return {
        "exit_reason": "timeout",
        "exit_price": last_row["close"],
        "exit_time": last_row["timestamp"],
        "bars_held_intrabar": bars_held,
        "ambiguous": False,
        "used_fallback": False,
    }
