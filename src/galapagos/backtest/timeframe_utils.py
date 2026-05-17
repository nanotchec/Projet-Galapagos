from __future__ import annotations

import re
from datetime import timedelta


def timeframe_to_timedelta(timeframe: str) -> timedelta:
    match = re.fullmatch(r"(\d+)([mhd])", timeframe.strip().lower())
    if not match:
        raise ValueError(f"Unsupported timeframe format: {timeframe}")
    value = int(match.group(1))
    unit = match.group(2)
    if value <= 0:
        raise ValueError("Timeframe value must be positive")
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    return timedelta(days=value)


def candle_close_time(open_timestamp, timeframe: str):
    return open_timestamp + timeframe_to_timedelta(timeframe)
