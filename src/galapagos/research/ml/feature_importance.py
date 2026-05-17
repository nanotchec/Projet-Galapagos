"""Feature importance extraction for ML research."""
from __future__ import annotations

from typing import Any

import numpy as np

FEATURE_GROUPS = {
    "ohlcv": ["return_lag_", "realized_vol_", "atr_", "volume_zscore",
              "dist_from_high", "dist_from_low", "trend_slope", "dist_ma_"],
    "macro": ["equity_market_trend", "liquidity_proxy", "vol_regime_vix",
              "term_spread", "credit_spread", "macro_confidence"],
    "derivatives": ["funding_rate", "long_short_ratio", "open_interest",
                    "premium", "taker_volume"],
    "alpha_score": ["alpha_score", "momentum_score", "breakout_score",
                    "volatility_quality_score", "regime_score",
                    "cost_penalty_score", "crowded_trade_penalty",
                    "missing_data_penalty"],
}


def _classify_feature(name: str) -> str:
    for group, patterns in FEATURE_GROUPS.items():
        if any(p in name for p in patterns):
            return group
    return "other"


def extract_feature_importance(
    model: Any, feature_names: list[str], *, top_n: int = 20,
) -> dict[str, Any]:
    importances: np.ndarray | None = None
    if hasattr(model, "feature_importances_"):
        importances = np.array(model.feature_importances_)
    elif hasattr(model, "coef_"):
        coef = np.array(model.coef_)
        if coef.ndim == 2:
            coef = coef[0]
        importances = np.abs(coef)
    else:
        return {"status": "not_supported", "model_type": type(model).__name__}
    if importances is None or len(importances) != len(feature_names):
        return {"status": "dimension_mismatch"}
    idx = np.argsort(importances)[::-1]
    top = [{"feature": feature_names[i], "importance": float(importances[i])}
           for i in idx[:top_n]]
    grp: dict[str, float] = {}
    for i, nm in enumerate(feature_names):
        g = _classify_feature(nm)
        grp[g] = grp.get(g, 0.0) + float(importances[i])
    total = sum(grp.values()) or 1.0
    return {"status": "computed", "top_features": top,
            "group_importance": grp,
            "group_importance_pct": {k: v / total for k, v in grp.items()}}
