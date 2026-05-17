from __future__ import annotations

from typing import Any

import pandas as pd


def _summary(frame: pd.DataFrame) -> dict[str, float]:
    p = pd.to_numeric(frame["predicted_probability_calibrated"], errors="coerce")
    return {
        "count": int(len(frame)),
        "mean": float(p.mean()),
        "median": float(p.median()),
        "q10": float(p.quantile(0.1)),
        "q50": float(p.quantile(0.5)),
        "q90": float(p.quantile(0.9)),
        "share_above_0_5": float((p > 0.5).mean()),
        "top_decile_mean": float(frame.loc[p >= p.quantile(0.9), "forward_return_12bar"].mean()) if len(frame) else None,
    }


def run_probability_distribution_shift(df: pd.DataFrame) -> dict[str, Any]:
    frame = df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    pre = frame[frame["timestamp"] < pd.Timestamp("2026-01-01")]
    recent = frame[frame["timestamp"] >= pd.Timestamp("2026-01-01")]
    pre_stats = _summary(pre)
    recent_stats = _summary(recent)
    status = (
        "PROBABILITY_DISTRIBUTION_SHIFT_DETECTED"
        if abs(recent_stats["mean"] - pre_stats["mean"]) > 0.005 or abs(recent_stats["q90"] - pre_stats["q90"]) > 0.01
        else "DISTRIBUTION_DIAGNOSTIC_LIMITED"
    )
    return {
        "pre_2026": pre_stats,
        "2026": recent_stats,
        "probability_distribution_shift_status": status,
    }
