from __future__ import annotations

from collections import defaultdict

import pandas as pd


def classify_regime_window(data: pd.DataFrame) -> dict:
    close = data["close"].astype(float)
    returns = close.pct_change().dropna()
    if len(close) < 3:
        return {"regime_label": "mixed", "return_pct": 0.0, "realized_volatility": 0.0}
    return_pct = float(close.iloc[-1] / close.iloc[0] - 1.0)
    volatility = float(returns.std()) if len(returns) else 0.0
    drawdown = float((close / close.cummax() - 1.0).min())
    if volatility > 0.04 or drawdown < -0.2:
        label = "high_volatility"
    elif return_pct > 0.05:
        label = "uptrend"
    elif return_pct < -0.05:
        label = "downtrend"
    elif volatility < 0.01:
        label = "low_volatility"
    else:
        label = "range"
    return {
        "regime_label": label,
        "return_pct": return_pct,
        "max_drawdown": drawdown,
        "realized_volatility": volatility,
    }


def classify_regime_per_candle(data: pd.DataFrame, window: int = 50) -> pd.DataFrame:
    output = data.copy()
    labels = []
    for index in range(len(output)):
        start = max(0, index - window + 1)
        labels.append(classify_regime_window(output.iloc[start : index + 1])["regime_label"])
    output["research_regime"] = labels
    return output


def aggregate_signal_quality_by_regime(signals: pd.DataFrame, labels: pd.DataFrame) -> dict:
    if signals.empty:
        return {}
    regimes = classify_regime_per_candle(labels)
    buckets: dict[str, list[float]] = defaultdict(list)
    for _, signal in signals.iterrows():
        index = int(signal.get("index", -1))
        if index < 0 or index >= len(regimes):
            continue
        value = regimes.iloc[index].get("forward_return_6bar")
        if pd.notna(value):
            buckets[str(regimes.iloc[index]["research_regime"])].append(float(value))
    return {
        regime: {
            "count": len(values),
            "mean_forward_return_6bar": sum(values) / len(values) if values else 0.0,
        }
        for regime, values in buckets.items()
    }

