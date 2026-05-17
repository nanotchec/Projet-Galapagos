from __future__ import annotations

from typing import Any

import pandas as pd


def run_cost_drag_diagnostic(df: pd.DataFrame) -> dict[str, Any]:
    frame = df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame["gross_return"] = pd.to_numeric(frame["forward_return_12bar"], errors="coerce")
    frame["net_return"] = frame["gross_return"] - pd.to_numeric(frame["cost_proxy"], errors="coerce")
    pre = frame[frame["timestamp"] < pd.Timestamp("2026-01-01")]
    recent = frame[frame["timestamp"] >= pd.Timestamp("2026-01-01")]
    gross_pre = float(pre["gross_return"].mean())
    gross_recent = float(recent["gross_return"].mean())
    net_pre = float(pre["net_return"].mean())
    net_recent = float(recent["net_return"].mean())
    cost_mean = float(frame["cost_proxy"].mean())
    if gross_recent <= 0 and net_recent <= gross_recent:
        status = "EDGE_NEGATIVE_BEFORE_COSTS"
    elif gross_recent > 0 and net_recent < 0:
        status = "COSTS_TURN_EDGE_NEGATIVE"
    else:
        status = "COST_DRAG_NOT_PRIMARY_DRIVER"
    return {
        "gross_mean_return_pre_2026": gross_pre,
        "gross_mean_return_2026": gross_recent,
        "net_mean_return_pre_2026": net_pre,
        "net_mean_return_2026": net_recent,
        "cost_proxy_mean": cost_mean,
        "edge_before_costs_pre_2026": gross_pre,
        "edge_before_costs_2026": gross_recent,
        "edge_after_costs_pre_2026": net_pre,
        "edge_after_costs_2026": net_recent,
        "cost_drag_status": status,
    }
