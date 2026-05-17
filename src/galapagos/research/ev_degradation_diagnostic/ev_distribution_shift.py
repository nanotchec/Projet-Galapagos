from __future__ import annotations

from typing import Any

import pandas as pd


def _summary(frame: pd.DataFrame) -> dict[str, float]:
    ev = pd.to_numeric(frame["ev_calibrated_proxy"], errors="coerce")
    return {
        "count": int(len(frame)),
        "mean": float(ev.mean()),
        "median": float(ev.median()),
        "q10": float(ev.quantile(0.1)),
        "q50": float(ev.quantile(0.5)),
        "q90": float(ev.quantile(0.9)),
        "share_positive_ev": float((ev > 0).mean()),
    }


def run_ev_distribution_shift(df: pd.DataFrame) -> dict[str, Any]:
    frame = df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    pre = frame[frame["timestamp"] < pd.Timestamp("2026-01-01")]
    recent = frame[frame["timestamp"] >= pd.Timestamp("2026-01-01")]
    pre_stats = _summary(pre)
    recent_stats = _summary(recent)
    status = (
        "EV_DISTRIBUTION_SHIFT_DETECTED"
        if recent_stats["mean"] < pre_stats["mean"] and recent_stats["q90"] < pre_stats["q90"]
        else "DISTRIBUTION_DIAGNOSTIC_LIMITED"
    )
    return {
        "pre_2026": pre_stats,
        "2026": recent_stats,
        "ev_distribution_shift_status": status,
    }
