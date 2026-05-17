from __future__ import annotations

from typing import Any

import pandas as pd


def split_periods(df: pd.DataFrame, *, timestamp_col: str = "timestamp") -> dict[str, pd.DataFrame]:
    frame = df.copy()
    frame[timestamp_col] = pd.to_datetime(frame[timestamp_col])
    periods = {
        "2024": ("2024-01-01", "2024-12-31"),
        "2025": ("2025-01-01", "2025-12-31"),
        "2026_H1": ("2026-01-01", "2026-06-30"),
        "pre_2026": ("2024-01-01", "2025-12-31"),
        "2026": ("2026-01-01", "2026-06-30"),
    }
    result: dict[str, pd.DataFrame] = {}
    for name, (start, end) in periods.items():
        mask = (frame[timestamp_col] >= pd.Timestamp(start)) & (frame[timestamp_col] <= pd.Timestamp(end))
        result[name] = frame.loc[mask].copy()
    return result
