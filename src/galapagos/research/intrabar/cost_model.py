"""Intrabar cost modeling and proxy metrics."""
from __future__ import annotations

from typing import Any

import pandas as pd


def evaluate_cost_stress(
    intrabar_df: pd.DataFrame, base_cost: float = 0.003
) -> dict[str, Any]:
    """Evaluate execution cost stress based on intrabar volatility."""
    if intrabar_df.empty:
        return {"verdict": "INTRABAR_COST_MODEL_INCONCLUSIVE", "details": {}}

    # High-low range proxy for volatility (not bid/ask spread)
    intrabar_df["hl_range"] = (intrabar_df["high"] - intrabar_df["low"]) / intrabar_df["open"]
    mean_range = intrabar_df["hl_range"].mean()

    # If intrabar volatility is high, fixed costs might be underestimating slippage
    verdict = "INTRABAR_COST_PROXY_AVAILABLE"
    if mean_range > 0.005:  # 0.5% average range per 5m candle is very high
        verdict = "COST_STRESS_STILL_DESTROYS_EDGE"

    return {
        "verdict": verdict,
        "note": "high-low range is not bid/ask spread. This is an intrabar_range_volatility_proxy.",
        "cost_proxy_type": "intrabar_range_volatility_proxy",
        "details": {
            "mean_intrabar_range_pct": float(mean_range),
            "base_cost_threshold": base_cost,
            "cost_stress_x2": base_cost * 2,
            "cost_stress_x3": base_cost * 3,
        },
    }
