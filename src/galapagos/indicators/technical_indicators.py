from __future__ import annotations

import pandas as pd


def compute_technical_indicators(df: pd.DataFrame) -> dict:
    close = df["close"]
    volume = df["volume"]
    sma_20 = close.rolling(20).mean().iloc[-1]
    sma_50 = close.rolling(50).mean().iloc[-1]
    volume_mean_20 = volume.rolling(20).mean().iloc[-1]
    return {
        "sma_20": float(sma_20) if pd.notna(sma_20) else None,
        "sma_50": float(sma_50) if pd.notna(sma_50) else None,
        "volume_mean_20": float(volume_mean_20) if pd.notna(volume_mean_20) else None,
        "last_close": float(close.iloc[-1]),
        "last_volume": float(volume.iloc[-1]),
    }

