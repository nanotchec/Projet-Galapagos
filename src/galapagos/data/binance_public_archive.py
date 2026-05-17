from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

BASE_URL = "https://data.binance.vision/data"
ALLOWED_SYMBOLS = {"BTCUSDT"}
ALLOWED_INTERVALS = {"4h", "1h", "5m", "1m"}
MARKET_PATHS = {
    "spot": "spot",
    "futures_um": "futures/um",
}


@dataclass(frozen=True)
class BinanceArchivePlan:
    url: str
    raw_path: Path
    silver_path: Path
    exists: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "raw_path": str(self.raw_path),
            "silver_path": str(self.silver_path),
            "exists": self.exists,
        }


def build_binance_archive_url(
    *,
    symbol: str,
    market: str,
    interval: str,
    year: int,
    month: int,
) -> str:
    _validate(symbol, market, interval)
    market_path = MARKET_PATHS[market]
    filename = f"{symbol}-{interval}-{year}-{month:02d}.zip"
    return f"{BASE_URL}/{market_path}/monthly/klines/{symbol}/{interval}/{filename}"


def plan_binance_ohlcv_download(
    *,
    symbol: str,
    market: str,
    interval: str,
    years: int,
    now: datetime | None = None,
) -> list[BinanceArchivePlan]:
    _validate(symbol, market, interval)
    now = now or datetime.now(UTC)
    start_year = now.year - max(years, 1) + 1
    plans = []
    for year in range(start_year, now.year + 1):
        last_month = now.month if year == now.year else 12
        for month in range(1, last_month + 1):
            url = build_binance_archive_url(
                symbol=symbol,
                market=market,
                interval=interval,
                year=year,
                month=month,
            )
            filename = url.rsplit("/", 1)[-1]
            raw_path = Path("data/raw/binance_public") / market / symbol / interval / filename
            silver_path = (
                Path("data/silver/ohlcv/binance")
                / symbol
                / interval
                / f"{symbol}_{interval}_{year}_{month:02d}.csv"
            )
            plans.append(
                BinanceArchivePlan(
                    url=url,
                    raw_path=raw_path,
                    silver_path=silver_path,
                    exists=raw_path.exists() or silver_path.exists(),
                )
            )
    return plans


def parse_binance_kline_csv(content: bytes | str) -> pd.DataFrame:
    raw = content.decode("utf-8") if isinstance(content, bytes) else content
    first_line = raw.splitlines()[0] if raw.splitlines() else ""
    has_header = "open_time" in first_line or "Open time" in first_line
    columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
        "ignore",
    ]
    frame = pd.read_csv(
        io.StringIO(raw),
        header=0 if has_header else None,
        names=None if has_header else columns,
    )
    if has_header:
        frame.columns = [str(column).strip().lower().replace(" ", "_") for column in frame.columns]
    frame["timestamp"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
    return frame[["timestamp", "open", "high", "low", "close", "volume"]].astype(
        {
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "float64",
        }
    )


def parse_binance_kline_zip(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".csv")]
        if not names:
            raise ValueError("No CSV file found in Binance archive.")
        with archive.open(names[0]) as handle:
            return parse_binance_kline_csv(handle.read())


def _validate(symbol: str, market: str, interval: str) -> None:
    if symbol not in ALLOWED_SYMBOLS:
        raise ValueError("V1.12 Binance archive downloader is BTCUSDT-only.")
    if market not in MARKET_PATHS:
        raise ValueError("market must be spot or futures_um.")
    if interval not in ALLOWED_INTERVALS:
        raise ValueError("Unsupported interval.")
