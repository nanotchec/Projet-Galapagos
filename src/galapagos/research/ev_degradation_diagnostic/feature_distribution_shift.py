from __future__ import annotations

from typing import Any

import pandas as pd


FEATURE_CANDIDATES = [
    "funding_rate",
    "funding_rate_binance",
    "funding_rate_bybit",
    "open_interest",
    "open_interest_bybit",
    "premium",
    "premium_binance",
    "premium_bybit",
    "taker_imbalance",
    "taker_buy_sell_ratio",
    "long_short_crowding",
    "derivatives_crowding_score",
    "derivatives_available_count",
    "derivatives_missing_count",
    "derivatives_confidence_score",
]


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _feature_shift(pre: pd.DataFrame, recent: pd.DataFrame, feature: str) -> dict[str, float] | None:
    if feature not in pre.columns and feature not in recent.columns:
        return None
    pre_s = _safe_numeric(pre.get(feature, pd.Series(dtype=float)))
    recent_s = _safe_numeric(recent.get(feature, pd.Series(dtype=float)))
    pre_mean = float(pre_s.mean()) if pre_s.notna().any() else None
    recent_mean = float(recent_s.mean()) if recent_s.notna().any() else None
    pre_miss = float(pre_s.isna().mean()) if len(pre_s) else None
    recent_miss = float(recent_s.isna().mean()) if len(recent_s) else None
    pre_std = float(pre_s.std()) if pre_s.notna().sum() > 1 else None
    if pre_mean is None or recent_mean is None:
        smd = None
    elif pre_std and pre_std > 0:
        smd = abs(recent_mean - pre_mean) / pre_std
    else:
        smd = None
    return {
        "feature": feature,
        "pre_2026_mean": pre_mean,
        "2026_mean": recent_mean,
        "pre_2026_missing_rate": pre_miss,
        "2026_missing_rate": recent_miss,
        "standardized_mean_difference": smd,
    }


def run_feature_distribution_shift(df: pd.DataFrame) -> dict[str, Any]:
    frame = df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    pre = frame[frame["timestamp"] < pd.Timestamp("2026-01-01")]
    recent = frame[frame["timestamp"] >= pd.Timestamp("2026-01-01")]
    shifts = []
    for feature in FEATURE_CANDIDATES:
        item = _feature_shift(pre, recent, feature)
        if item is not None:
            shifts.append(item)
    shifts = sorted(
        shifts,
        key=lambda x: (
            x["standardized_mean_difference"] is None,
            -(x["standardized_mean_difference"] or 0.0),
            -(abs((x["2026_missing_rate"] or 0.0) - (x["pre_2026_missing_rate"] or 0.0))),
        ),
    )
    status = "FEATURE_DISTRIBUTION_SHIFT_DETECTED" if any((x["standardized_mean_difference"] or 0.0) > 0.25 for x in shifts) else "DISTRIBUTION_DIAGNOSTIC_LIMITED"
    return {
        "feature_shifts": shifts[:10],
        "feature_distribution_shift_status": status,
    }
