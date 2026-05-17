from __future__ import annotations

import pandas as pd


def build_macro_features(records: pd.DataFrame, timeframe: str = "4h") -> pd.DataFrame:
    if records.empty:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "available_timestamp",
                "macro_regime",
                "macro_confidence",
                "timeframe",
            ]
        )
    pivot = records.pivot_table(
        index="available_timestamp",
        columns="series_id",
        values="value",
        aggfunc="last",
    ).sort_index()
    features = pivot.ffill().reset_index()
    features["timestamp"] = pd.to_datetime(features["available_timestamp"], utc=True)
    features["timeframe"] = timeframe
    features["yield_curve_slope"] = features.get("DGS10", pd.Series(dtype=float)) - features.get(
        "DGS2",
        pd.Series(dtype=float),
    )
    features["vol_regime_vix"] = features.get("VIXCLS", pd.Series(dtype=float)).apply(
        lambda value: "high" if pd.notna(value) and value >= 25 else "normal"
    )
    features["rates_pressure"] = features.get("DGS10", pd.Series(dtype=float)).diff()
    features["equity_market_trend"] = features.get("SP500", pd.Series(dtype=float)).pct_change(20)
    features["macro_regime"] = features.apply(_macro_regime, axis=1)
    features["macro_confidence"] = 0.5
    features["macro_last_updated"] = features["available_timestamp"]
    return features


def _macro_regime(row: pd.Series) -> str:
    vix = row.get("VIXCLS")
    equity_trend = row.get("equity_market_trend")
    if pd.isna(vix) and pd.isna(equity_trend):
        return "unknown"
    if pd.notna(vix) and vix >= 30:
        return "risk_off"
    if pd.notna(equity_trend) and equity_trend > 0:
        return "risk_on"
    if pd.notna(equity_trend) and equity_trend < -0.03:
        return "risk_off"
    return "neutral"
