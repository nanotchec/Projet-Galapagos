"""Confidence/probability analysis for signal selection."""
from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_confidence(features: pd.DataFrame) -> dict[str, Any]:
    if features.empty or "predicted_probability" not in features:
        return {
            "buckets": [],
            "verdicts": ["CONFIDENCE_SIGNAL_WEAK"],
            "missing_columns": ["predicted_probability"],
        }
    rows = []
    for policy, policy_frame in features.groupby("policy"):
        work = policy_frame.copy()
        work["prob_bucket"] = pd.qcut(
            pd.to_numeric(work["predicted_probability"], errors="coerce").rank(method="first"),
            q=5,
            labels=["bottom_20", "20_40", "40_60", "60_80", "top_20"],
        )
        for bucket, group in work.groupby("prob_bucket", observed=False):
            rows.append(
                {
                    "policy": policy,
                    "bucket": str(bucket),
                    "count": int(len(group)),
                    "prob_min": float(group["predicted_probability"].min()),
                    "prob_max": float(group["predicted_probability"].max()),
                    "net_mean_pnl_pct": float(group["net_pnl_pct"].mean()),
                    "gross_mean_pnl_pct": float(group["gross_pnl_pct"].mean()),
                    "cost_viability_rate": float(group.get("is_cost_viable", False).mean()),
                }
            )
    verdicts = []
    for policy in features["policy"].dropna().unique():
        policy_rows = [r for r in rows if r["policy"] == policy]
        means = [r["net_mean_pnl_pct"] for r in policy_rows]
        if len(means) >= 2 and any(b < a for a, b in zip(means, means[1:], strict=False)):
            verdicts.append("CONFIDENCE_NOT_MONOTONIC")
        top = next((r for r in policy_rows if r["bucket"] == "top_20"), None)
        if top and top["net_mean_pnl_pct"] > 0 and top["count"] >= 30:
            verdicts.append("TOP_BUCKET_PROMISING_BUT_UNVALIDATED")
    if not verdicts:
        verdicts = ["CONFIDENCE_FILTER_FAILS_AFTER_COSTS", "CONFIDENCE_SIGNAL_WEAK"]
    return {"buckets": rows, "verdicts": sorted(set(verdicts))}
