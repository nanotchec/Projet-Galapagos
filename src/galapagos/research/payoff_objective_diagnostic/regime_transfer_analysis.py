"""Regime transfer diagnostics for payoff-objective failure."""
from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_regime_transfer(analysis_frame: pd.DataFrame, score_report: dict[str, Any]) -> dict[str, Any]:
    score_frame = score_report.get("score_frame_2026", pd.DataFrame()).copy()
    if score_frame.empty:
        return {
            "regime_transfer_status": "REGIME_TRANSFER_DIAGNOSTIC_LIMITED",
            "regime_column": None,
            "rows": [],
        }
    score_frame["timestamp"] = pd.to_datetime(score_frame["timestamp"], utc=True)
    regime_column = "macro_regime" if "macro_regime" in score_frame.columns else None
    if regime_column is None:
        return {
            "regime_transfer_status": "REGIME_TRANSFER_DIAGNOSTIC_LIMITED",
            "regime_column": regime_column,
            "rows": [],
        }
    recent = score_frame.copy()
    if recent.empty:
        return {
            "regime_transfer_status": "REGIME_TRANSFER_DIAGNOSTIC_LIMITED",
            "regime_column": regime_column,
            "rows": [],
        }
    rows = []
    for regime, subset in recent.groupby(regime_column):
        rows.append(
            {
                "regime": str(regime),
                "count": int(len(subset)),
                "mean_net_return": float(pd.to_numeric(subset.get("net_return"), errors="coerce").fillna(0.0).mean()),
                "mean_gross_return": float(pd.to_numeric(subset.get("gross_return"), errors="coerce").fillna(0.0).mean()),
                "mean_cost_proxy": float(pd.to_numeric(subset.get("cost_proxy"), errors="coerce").fillna(0.0).mean()),
            }
        )
    dominant = max(rows, key=lambda row: row["count"]) if rows else None
    if dominant and dominant["mean_net_return"] <= 0:
        status = "PAYOFF_OBJECTIVE_FAILS_IN_2026_REGIME"
    elif dominant and dominant["count"] > 0:
        status = "REGIME_TRANSFER_NOT_PRIMARY_DRIVER"
    else:
        status = "REGIME_TRANSFER_DIAGNOSTIC_LIMITED"
    return {
        "regime_transfer_status": status,
        "regime_column": regime_column,
        "rows": rows,
        "dominant_2026_regime": dominant["regime"] if dominant else None,
        "dominant_2026_regime_count": dominant["count"] if dominant else 0,
        "dominant_2026_mean_net_return": dominant["mean_net_return"] if dominant else 0.0,
    }
