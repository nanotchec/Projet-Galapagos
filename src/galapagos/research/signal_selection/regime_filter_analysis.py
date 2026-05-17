"""Regime analysis for signal selection."""
from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_regime_filters(features: pd.DataFrame, sweep: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    if features.empty:
        return {"rows": [], "verdicts": ["NO_REGIME_SELECTION_EDGE"]}
    for policy, policy_frame in features.groupby("policy"):
        regime_columns = [
            "volatility_regime",
            "trend_regime",
            "macro_regime",
            "derivatives_risk_regime",
        ]
        for regime_col in regime_columns:
            if regime_col not in policy_frame:
                continue
            for regime, group in policy_frame.groupby(regime_col, dropna=False):
                rows.append(
                    {
                        "policy": policy,
                        "regime_field": regime_col,
                        "regime": str(regime),
                        "count": int(len(group)),
                        "net_mean_pnl_pct": float(group["net_pnl_pct"].mean()),
                        "gross_mean_pnl_pct": float(group["gross_pnl_pct"].mean()),
                        "win_rate": float((group["net_pnl_pct"] > 0).mean()),
                        "cost_viability_rate": float(group.get("is_cost_viable", False).mean()),
                    }
                )
    verdicts = ["NO_REGIME_SELECTION_EDGE"]
    high_vol = [
        r
        for r in rows
        if r["regime_field"] == "volatility_regime" and r["regime"] == "high"
    ]
    if high_vol and all(r["net_mean_pnl_pct"] < 0 for r in high_vol):
        verdicts = ["HIGH_VOL_SHOULD_BE_EXCLUDED", "REGIME_FILTER_PROMISING_BUT_UNVALIDATED"]
    regime_rules = [r for r in sweep if r.get("rule_family") == "regime"]
    if any(
        r.get("net_mean_pnl_pct", 0) > 0 and r.get("selected_count", 0) >= 30
        for r in regime_rules
    ):
        verdicts = ["REGIME_FILTER_PROMISING_BUT_UNVALIDATED"]
    return {"rows": rows, "verdicts": verdicts}
