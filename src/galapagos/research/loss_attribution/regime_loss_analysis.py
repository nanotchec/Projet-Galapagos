from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_regimes(df: pd.DataFrame, ohlcv_4h: pd.DataFrame) -> dict[str, Any]:
    """Analyze performance across market regimes."""
    if df.empty:
        return {}
        
    # Merge with regimes from dataset if available
    # For now, let's derive simple regimes if not present
    if "trend_regime" not in ohlcv_4h.columns:
        # Simple SMA-based trend
        ohlcv_4h = ohlcv_4h.copy()
        ohlcv_4h["sma_20"] = ohlcv_4h["close"].rolling(20).mean()
        ohlcv_4h["trend_regime"] = "range"
        ohlcv_4h.loc[ohlcv_4h["close"] > ohlcv_4h["sma_20"] * 1.01, "trend_regime"] = "uptrend"
        ohlcv_4h.loc[ohlcv_4h["close"] < ohlcv_4h["sma_20"] * 0.99, "trend_regime"] = "downtrend"
        
    if "volatility_regime" not in ohlcv_4h.columns:
        # Simple ATR-based volatility
        ohlcv_4h["tr"] = (ohlcv_4h["high"] - ohlcv_4h["low"]) / ohlcv_4h["close"]
        ohlcv_4h["atr"] = ohlcv_4h["tr"].rolling(20).mean()
        ohlcv_4h["volatility_regime"] = "normal"
        ohlcv_4h.loc[ohlcv_4h["tr"] > ohlcv_4h["atr"] * 1.5, "volatility_regime"] = "high"
        ohlcv_4h.loc[ohlcv_4h["tr"] < ohlcv_4h["atr"] * 0.7, "volatility_regime"] = "low"

    # Merge df with ohlcv_4h on timestamp
    merged = pd.merge_asof(
        df.sort_values("timestamp"),
        ohlcv_4h[["timestamp", "trend_regime", "volatility_regime"]].sort_values("timestamp"),
        on="timestamp",
        direction="backward"
    )
    
    trend_stats = merged.groupby("trend_regime")["net_pnl_pct"].agg(["count", "mean", "sum"]).to_dict(orient="index")
    vol_stats = merged.groupby("volatility_regime")["net_pnl_pct"].agg(["count", "mean", "sum"]).to_dict(orient="index")
    
    verdict = "NO_REGIME_EDGE"
    if "uptrend" in trend_stats and trend_stats["uptrend"]["mean"] > 0:
        verdict = "EDGE_ONLY_IN_UPTREND"
    elif "high" in vol_stats and vol_stats["high"]["mean"] < df["net_pnl_pct"].mean() * 2:
        verdict = "HIGH_VOL_DESTROYS_EDGE"
        
    return {
        "trend_regimes": trend_stats,
        "volatility_regimes": vol_stats,
        "verdict": verdict
    }
