from __future__ import annotations


def detect_market_regime(indicators: dict, volatility: float | None) -> dict:
    sma_20 = indicators.get("sma_20")
    sma_50 = indicators.get("sma_50")
    if volatility is not None and volatility > 0.04:
        vol_regime = "extreme"
    elif volatility is not None and volatility > 0.02:
        vol_regime = "high"
    elif volatility is not None and volatility < 0.005:
        vol_regime = "low"
    else:
        vol_regime = "normal"
    if sma_20 is None or sma_50 is None:
        trend = "unknown"
    elif sma_20 > sma_50:
        trend = "uptrend"
    elif sma_20 < sma_50:
        trend = "downtrend"
    else:
        trend = "range"
    return {"trend": trend, "volatility_regime": vol_regime}

