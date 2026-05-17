"""Score decile diagnostics for the payoff-objective failure case."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def analyze_score_deciles(
    candidate_rebuild: dict[str, Any],
) -> dict[str, Any]:
    scored = candidate_rebuild.get("score_frame_2026", pd.DataFrame()).copy()
    if scored.empty:
        return {
            "score_decile_status": "SCORE_DECILES_DIAGNOSTIC_INCONCLUSIVE",
            "candidate_name": candidate_rebuild.get("candidate_name"),
            "split_name": "2026_H1",
            "selection_count": 0,
            "decile_means": [],
            "buckets": [],
            "top_10_mean_return": 0.0,
            "top_10_downside_rate": 0.0,
            "top_10_payoff_ratio": 0.0,
            "spearman_2026": 0.0,
            "monotonic": False,
            "selected_count_2026": 0,
            "top_score_return_mean": 0.0,
            "top_score_gross_return_mean": 0.0,
            "top_score_cost_proxy_mean": 0.0,
            "recent_window_status": "RECENT_WINDOW_INCONCLUSIVE",
        }

    scored["timestamp"] = pd.to_datetime(scored["timestamp"], utc=True)
    scored["net_return"] = pd.to_numeric(scored["net_return"], errors="coerce").fillna(0.0)
    scored["gross_return"] = pd.to_numeric(scored["gross_return"], errors="coerce").fillna(0.0)
    scored["cost_proxy"] = pd.to_numeric(scored["cost_proxy"], errors="coerce").fillna(0.0)
    scored = scored.sort_values("score", ascending=False).reset_index(drop=True)
    scored["decile"] = pd.qcut(
        scored["score"].rank(method="first", ascending=False),
        q=min(10, len(scored)),
        labels=False,
        duplicates="drop",
    )
    bucket_specs = [(0.01, "top_1pct"), (0.05, "top_5pct"), (0.10, "top_10pct"), (0.20, "top_20pct")]
    buckets = []
    for frac, label in bucket_specs:
        count = max(1, int(round(len(scored) * frac)))
        subset = scored.head(count)
        positive = subset["net_return"] > 0
        negative = subset["net_return"] < 0
        buckets.append(
            {
                "bucket": label,
                "count": int(len(subset)),
                "mean_return": float(subset["net_return"].mean()) if len(subset) else 0.0,
                "median_return": float(subset["net_return"].median()) if len(subset) else 0.0,
                "downside_rate": float((subset["net_return"] < 0).mean()) if len(subset) else 0.0,
                "payoff_ratio": float(abs(subset.loc[positive, "net_return"].mean()) / abs(subset.loc[negative, "net_return"].mean()))
                if len(subset) and positive.any() and negative.any()
                else 0.0,
                "gross_mean_return": float(subset["gross_return"].mean()) if len(subset) else 0.0,
                "net_mean_return": float(subset["net_return"].mean()) if len(subset) else 0.0,
            }
        )
    decile_means = [
        float(group["net_return"].mean())
        for _, group in scored.groupby("decile", sort=True)
    ] if len(scored) >= 10 else [float(scored["net_return"].mean())]
    monotonic = all(left >= right - 1e-12 for left, right in zip(decile_means, decile_means[1:])) if len(decile_means) > 1 else False
    if not monotonic:
        status = "SCORE_DECILES_NON_MONOTONIC_2026"
    elif buckets[2]["mean_return"] <= 0:
        status = "SCORE_DECILES_WEAK_BUT_ORDERED"
    else:
        status = "SCORE_DECILES_DIAGNOSTIC_INCONCLUSIVE"
    top_10_count = max(1, int(round(len(scored) * 0.10)))
    top_10 = scored.head(top_10_count)
    return {
        "score_decile_status": status,
        "candidate_name": candidate_rebuild.get("candidate_name"),
        "split_name": "2026_H1",
        "selection_count": int(len(scored)),
        "decile_means": decile_means,
        "buckets": buckets,
        "top_10_mean_return": buckets[2]["mean_return"],
        "top_10_downside_rate": buckets[2]["downside_rate"],
        "top_10_payoff_ratio": buckets[2]["payoff_ratio"],
        "spearman_2026": float(pd.Series(scored["score"]).corr(scored["net_return"], method="spearman")) if len(scored) > 1 else 0.0,
        "monotonic": monotonic,
        "selected_count_2026": int(len(scored)),
        "top_score_return_mean": float(top_10["net_return"].mean()) if len(scored) else 0.0,
        "top_score_gross_return_mean": float(top_10["gross_return"].mean()) if len(scored) else 0.0,
        "top_score_cost_proxy_mean": float(top_10["cost_proxy"].mean()) if len(scored) else 0.0,
        "top_score_downside_rate": float((top_10["net_return"] < 0).mean()) if len(scored) else 0.0,
        "recent_window_status": "RECENT_WINDOW_WEAK" if buckets[2]["mean_return"] <= 0 else "RECENT_WINDOW_INCONCLUSIVE",
    }
