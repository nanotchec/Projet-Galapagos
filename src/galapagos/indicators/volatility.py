from __future__ import annotations

import pandas as pd


def realized_volatility(df: pd.DataFrame, window: int = 20) -> float | None:
    returns = df["close"].pct_change()
    value = returns.rolling(window).std().iloc[-1]
    return float(value) if pd.notna(value) else None

