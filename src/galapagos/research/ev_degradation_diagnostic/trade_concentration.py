from __future__ import annotations

from typing import Any

import math
import pandas as pd


def run_trade_concentration(df: pd.DataFrame) -> dict[str, Any]:
    frame = df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame["net_proxy"] = pd.to_numeric(frame["forward_return_12bar"], errors="coerce") - pd.to_numeric(
        frame["cost_proxy"], errors="coerce"
    )
    losses = frame[frame["net_proxy"] < 0].sort_values("net_proxy")
    abs_total = float(-losses["net_proxy"].sum()) if not losses.empty else 0.0
    shares = {}
    for frac in (0.01, 0.05, 0.1):
        n = max(1, math.ceil(len(losses) * frac)) if len(losses) else 0
        shares[f"top_{int(frac*100)}_loss_share"] = float((-losses.head(n)["net_proxy"].sum() / abs_total)) if abs_total else 0.0
    monthly = frame.assign(month=frame["timestamp"].dt.to_period("M")).groupby("month")["net_proxy"].sum()
    negative_months = int((monthly < 0).sum())
    status = "LOSSES_CONCENTRATED_IN_OUTLIERS" if shares.get("top_10_loss_share", 0.0) >= 0.25 else "LOSSES_DIFFUSE"
    return {
        "negative_trade_count": int((frame["net_proxy"] < 0).sum()),
        "negative_months": negative_months,
        "monthly_net_sum": {str(k): float(v) for k, v in monthly.items()},
        **shares,
        "trade_concentration_status": status,
    }
