from __future__ import annotations

from typing import Any

import pandas as pd


def run_ev_realization_gap(df: pd.DataFrame) -> dict[str, Any]:
    frame = df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame["realized_net_proxy"] = pd.to_numeric(frame["forward_return_12bar"], errors="coerce") - pd.to_numeric(
        frame["cost_proxy"], errors="coerce"
    )
    pre = frame[frame["timestamp"] < pd.Timestamp("2026-01-01")]
    recent = frame[frame["timestamp"] >= pd.Timestamp("2026-01-01")]
    pre_pred = float(pd.to_numeric(pre["ev_calibrated_proxy"], errors="coerce").mean())
    pre_real = float(pd.to_numeric(pre["realized_net_proxy"], errors="coerce").mean())
    recent_pred = float(pd.to_numeric(recent["ev_calibrated_proxy"], errors="coerce").mean())
    recent_real = float(pd.to_numeric(recent["realized_net_proxy"], errors="coerce").mean())
    pre_gap = pre_real - pre_pred
    recent_gap = recent_real - recent_pred
    status = (
        "EV_PROXY_OVERESTIMATES_2026"
        if recent_pred > recent_real and abs(recent_gap) > abs(pre_gap)
        else "EV_PROXY_STABLE"
        if abs(recent_gap - pre_gap) < 0.001
        else "EV_REALIZATION_GAP_INCONCLUSIVE"
    )
    return {
        "mean_predicted_ev_pre_2026": pre_pred,
        "mean_realized_return_pre_2026": pre_real,
        "ev_realization_gap_pre_2026": pre_gap,
        "mean_predicted_ev_2026": recent_pred,
        "mean_realized_return_2026": recent_real,
        "ev_realization_gap_2026": recent_gap,
        "ev_overestimation_2026": recent_pred - recent_real,
        "ev_realization_gap_status": status,
    }
