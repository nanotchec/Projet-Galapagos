"""Downside miss analysis for payoff-objective failure."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def analyze_downside_miss(analysis_frame: pd.DataFrame, score_report: dict[str, Any]) -> dict[str, Any]:
    score_frame = score_report.get("score_frame_2026", pd.DataFrame()).copy()
    if score_frame.empty:
        return {"downside_miss_status": "DOWNSIDE_DIAGNOSTIC_INCONCLUSIVE", "issues": ["no scored 2026 frame"]}
    score_frame = score_frame.sort_values("score", ascending=False).reset_index(drop=True)
    top_10 = score_frame.head(max(1, int(round(len(score_frame) * 0.1))))
    top_10_mean = float(top_10["net_return"].mean()) if len(top_10) else 0.0
    net = pd.to_numeric(score_frame.get("net_return"), errors="coerce").fillna(0.0)
    gross = pd.to_numeric(score_frame.get("gross_return"), errors="coerce").fillna(0.0)
    losses = score_frame.loc[net < 0].copy()
    if losses.empty:
        return {
            "downside_miss_status": "DOWNSIDE_DIAGNOSTIC_INCONCLUSIVE",
            "top_10_mean_return": top_10_mean,
            "loss_count": 0,
        }
    worst = losses.nsmallest(max(1, int(round(len(losses) * 0.1))), "net_return")
    worst_5 = losses.nsmallest(max(1, int(round(len(losses) * 0.05))), "net_return")
    worst_1 = losses.nsmallest(max(1, int(round(len(losses) * 0.01))), "net_return")
    total_negative = abs(float(net[net < 0].sum())) or 1.0
    negative_mass = {
        "top_1pct": float(abs(worst_1["net_return"].sum()) / total_negative),
        "top_5pct": float(abs(worst_5["net_return"].sum()) / total_negative),
        "top_10pct": float(abs(worst["net_return"].sum()) / total_negative),
    }
    if top_10_mean <= 0 or negative_mass["top_5pct"] > 0.35:
        status = "DOWNSIDE_RISK_NOT_FILTERED_2026"
    elif negative_mass["top_10pct"] > 0.2:
        status = "DOWNSIDE_RISK_PARTIALLY_FILTERED"
    else:
        status = "DOWNSIDE_DIAGNOSTIC_INCONCLUSIVE"
    return {
        "downside_miss_status": status,
        "loss_count": int(len(losses)),
        "worst_1pct_count": int(len(worst_1)),
        "worst_5pct_count": int(len(worst_5)),
        "worst_10pct_count": int(len(worst)),
        "negative_mass": negative_mass,
        "top_10_mean_return": top_10_mean,
        "worst_loss_score_mean": float(worst["score"].mean()) if len(worst) else 0.0,
        "worst_loss_return_mean": float(worst["net_return"].mean()) if len(worst) else 0.0,
        "gross_mean_return_2026": float(gross.mean()) if len(gross) else 0.0,
    }
