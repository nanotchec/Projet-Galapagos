from __future__ import annotations

import pandas as pd


def align_derivatives_asof(
    base: pd.DataFrame,
    features: pd.DataFrame,
    *,
    tolerance: str | None = None,
) -> pd.DataFrame:
    if features.empty:
        return base.copy()
    left = base.sort_values("timestamp").copy()
    right = features.sort_values("available_timestamp").copy()
    left["timestamp"] = pd.to_datetime(left["timestamp"], utc=True)
    right["available_timestamp"] = pd.to_datetime(right["available_timestamp"], utc=True)
    aligned = pd.merge_asof(
        left,
        right,
        left_on="timestamp",
        right_on="available_timestamp",
        direction="backward",
        tolerance=pd.Timedelta(tolerance) if tolerance else None,
    )
    if (aligned["available_timestamp"] > aligned["timestamp"]).fillna(False).any():
        raise ValueError("Future derivatives feature detected.")
    return aligned
