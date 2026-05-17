from __future__ import annotations

from typing import Any

import pandas as pd


class KrakenCollector:
    def __init__(self) -> None:
        import ccxt

        self.exchange = ccxt.kraken({"enableRateLimit": True})

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 250) -> pd.DataFrame:
        rows = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])


def mock_ohlcv(limit: int = 250, start_price: float = 65_000.0) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    price = start_price
    for idx in range(limit):
        drift = (idx % 10 - 4.5) * 8
        close = price + drift
        rows.append(
            {
                "timestamp": idx,
                "open": price,
                "high": max(price, close) + 120,
                "low": min(price, close) - 120,
                "close": close,
                "volume": 100 + idx % 25,
            }
        )
        price = close
    return pd.DataFrame(rows)

