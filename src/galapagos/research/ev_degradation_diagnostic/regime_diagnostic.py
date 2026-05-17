from __future__ import annotations

from typing import Any

import pandas as pd


def run_regime_diagnostic(df: pd.DataFrame) -> dict[str, Any]:
    frame = df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    regime_col = "derivatives_risk_regime" if "derivatives_risk_regime" in frame.columns else None
    if regime_col is None:
        return {"regime_degradation_status": "REGIME_DATA_LIMITED", "regime_available": False}
    frame["net_proxy"] = pd.to_numeric(frame["forward_return_12bar"], errors="coerce") - pd.to_numeric(
        frame["cost_proxy"], errors="coerce"
    )
    pre = frame[frame["timestamp"] < pd.Timestamp("2026-01-01")]
    recent = frame[frame["timestamp"] >= pd.Timestamp("2026-01-01")]
    pre_counts = pre[regime_col].value_counts(dropna=False).to_dict()
    recent_counts = recent[regime_col].value_counts(dropna=False).to_dict()
    pre_perf = pre.groupby(regime_col)["net_proxy"].agg(["count", "mean", "median"]).to_dict("index")
    recent_perf = recent.groupby(regime_col)["net_proxy"].agg(["count", "mean", "median"]).to_dict("index")
    status = "REGIME_NOT_PRIMARY_DRIVER"
    if recent_counts:
        top_regime = max(recent_counts, key=recent_counts.get)
        top_share = recent_counts[top_regime] / max(1, len(recent))
        if top_share > 0.8 and float(recent_perf.get(top_regime, {}).get("mean", 0.0) or 0.0) < 0:
            status = "REGIME_EXPLAINS_DEGRADATION"
    return {
        "regime_available": True,
        "regime_column": regime_col,
        "pre_2026_counts": pre_counts,
        "2026_counts": recent_counts,
        "pre_2026_performance": pre_perf,
        "2026_performance": recent_perf,
        "regime_degradation_status": status,
    }
