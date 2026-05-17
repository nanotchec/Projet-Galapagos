"""Align intrabar data to parent 4h timeframe."""
from __future__ import annotations

from typing import Any

import pandas as pd


def get_intrabar_slice(
    intrabar_df: pd.DataFrame, parent_open_time: pd.Timestamp, parent_close_time: pd.Timestamp
) -> pd.DataFrame:
    """Get the subset of intrabar data that falls strictly within the parent candle."""
    # Ensure timezone awareness
    if not parent_open_time.tzinfo:
        parent_open_time = parent_open_time.tz_localize("UTC")
    if not parent_close_time.tzinfo:
        parent_close_time = parent_close_time.tz_localize("UTC")

    mask = (intrabar_df["timestamp"] >= parent_open_time) & (
        intrabar_df["timestamp"] < parent_close_time
    )
    return intrabar_df[mask].copy()


def validate_intrabar_coverage(
    parent_open_time: pd.Timestamp,
    parent_close_time: pd.Timestamp,
    intrabar_slice: pd.DataFrame,
    intrabar_tf: str = "5m",
) -> dict[str, Any]:
    """Validate coverage of the intrabar slice.

    4h = 240 minutes.
    5m tf = 48 candles expected.
    1m tf = 240 candles expected.
    """
    expected = 48 if intrabar_tf == "5m" else 240

    found = len(intrabar_slice)
    coverage_pct = found / expected if expected > 0 else 0.0

    status = "complete"
    if coverage_pct < 0.90:
        status = "partial" if coverage_pct > 0 else "missing"

    return {
        "expected_candles": expected,
        "found_candles": found,
        "coverage_pct": coverage_pct,
        "status": status,
    }


def align_intrabar_to_parent(
    parent_df: pd.DataFrame,
    intrabar_df: pd.DataFrame,
    intrabar_tf: str = "5m",
    parent_tf: str = "4h",
) -> dict[str, Any]:
    """Align the full intrabar dataset against the parent dataset.

    Returns a dictionary mapping parent timestamp to its intrabar slice and coverage metrics.
    """
    if not pd.api.types.is_datetime64_any_dtype(parent_df["timestamp"]):
        parent_df["timestamp"] = pd.to_datetime(parent_df["timestamp"], utc=True)

    if not pd.api.types.is_datetime64_any_dtype(intrabar_df["timestamp"]):
        intrabar_df["timestamp"] = pd.to_datetime(intrabar_df["timestamp"], utc=True)

    results = {}

    intrabar_df = intrabar_df.sort_values("timestamp")

    parent_delta = pd.Timedelta(hours=4)

    total_candles = 0
    complete_candles = 0
    missing_candles = 0
    partial_candles = 0

    for _, row in parent_df.iterrows():
        open_time = row["timestamp"]
        close_time = open_time + parent_delta

        slice_df = get_intrabar_slice(intrabar_df, open_time, close_time)
        val = validate_intrabar_coverage(open_time, close_time, slice_df, intrabar_tf)

        total_candles += 1
        if val["status"] == "complete":
            complete_candles += 1
        elif val["status"] == "partial":
            partial_candles += 1
        else:
            missing_candles += 1

        results[open_time] = {"slice": slice_df, "coverage": val}

    return {
        "aligned_data": results,
        "metrics": {
            "total_parent_candles": total_candles,
            "complete_candles": complete_candles,
            "partial_candles": partial_candles,
            "missing_candles": missing_candles,
            "overall_coverage_ratio": complete_candles / total_candles if total_candles else 0.0,
        },
    }
