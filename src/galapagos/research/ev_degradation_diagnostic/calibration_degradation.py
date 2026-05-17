from __future__ import annotations

from typing import Any

import pandas as pd


def _brier_ece(frame: pd.DataFrame) -> dict[str, float]:
    p = pd.to_numeric(frame["predicted_probability_calibrated"], errors="coerce").clip(0, 1)
    y = pd.to_numeric(frame["actual_target"], errors="coerce")
    valid = p.notna() & y.notna()
    if not valid.any():
        return {"brier": float("nan"), "ece": float("nan")}
    p = p[valid]
    y = y[valid]
    brier = float(((p - y) ** 2).mean())
    bins = pd.qcut(p.rank(method="first"), q=min(10, len(p)), labels=False, duplicates="drop")
    ece = 0.0
    for bucket in sorted(set(bins.dropna())):
        mask = bins == bucket
        ece += abs(float(y[mask].mean()) - float(p[mask].mean())) * (mask.sum() / len(p))
    return {"brier": brier, "ece": float(ece)}


def run_calibration_degradation(df: pd.DataFrame) -> dict[str, Any]:
    frame = df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    pre = frame[frame["timestamp"] < pd.Timestamp("2026-01-01")]
    recent = frame[frame["timestamp"] >= pd.Timestamp("2026-01-01")]
    pre_stats = _brier_ece(pre)
    recent_stats = _brier_ece(recent)
    if any(pd.isna(v) for v in [pre_stats["brier"], pre_stats["ece"], recent_stats["brier"], recent_stats["ece"]]):
        status = "CALIBRATION_DIAGNOSTIC_LIMITED"
    elif recent_stats["brier"] > pre_stats["brier"] and recent_stats["ece"] > pre_stats["ece"]:
        status = "CALIBRATION_DEGRADED_2026"
    elif recent_stats["brier"] <= pre_stats["brier"] and recent_stats["ece"] > pre_stats["ece"]:
        status = "CALIBRATION_STABLE_BUT_PAYOFF_DEGRADED"
    else:
        status = "CALIBRATION_DIAGNOSTIC_LIMITED"
    return {
        "pre_2026": pre_stats,
        "2026": recent_stats,
        "calibration_degradation_status": status,
    }
