from __future__ import annotations

import io
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import pandas as pd

from galapagos.data.public_market.config import ALLOWED_PUBLIC_HOSTS, BINANCE_PUBLIC_HOST


KLINE_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "ignore",
]


def build_public_archive_url(*, market_type: str, symbol: str, timeframe: str, date: str) -> str:
    if market_type != "spot":
        raise ValueError("V2.3 supports Binance spot public archive only.")
    return (
        f"https://{BINANCE_PUBLIC_HOST}/data/spot/daily/klines/"
        f"{symbol}/{timeframe}/{symbol}-{timeframe}-{date}.zip"
    )


def download_public_archive(url: str, destination: Path, *, timeout_seconds: int = 60) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in ALLOWED_PUBLIC_HOSTS:
        raise ValueError("V2.3 allows public read-only downloads from data.binance.vision only.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "galapagos-v2.3-public-read-only"})
    with urlopen(request, timeout=timeout_seconds) as response:
        if getattr(response, "status", 200) != 200:
            raise RuntimeError(f"public archive download failed with status {response.status}")
        destination.write_bytes(response.read())


def parse_binance_kline_zip(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError("Expected exactly one CSV file inside Binance daily archive.")
        with archive.open(csv_names[0]) as handle:
            return parse_binance_kline_csv(handle.read())


def parse_binance_kline_csv(content: bytes | str) -> pd.DataFrame:
    text = content.decode("utf-8") if isinstance(content, bytes) else content
    first_line = text.splitlines()[0] if text.splitlines() else ""
    has_header = "open_time" in first_line.lower() or "open time" in first_line.lower()
    frame = pd.read_csv(
        io.StringIO(text),
        header=0 if has_header else None,
        names=None if has_header else KLINE_COLUMNS,
    )
    frame.columns = [str(column).strip().lower().replace(" ", "_") for column in frame.columns]
    for column in KLINE_COLUMNS:
        if column not in frame.columns:
            raise ValueError(f"Missing Binance kline column: {column}")
    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame["trade_count"] = pd.to_numeric(frame["trade_count"], errors="raise").astype("int64")
    frame["open_time"] = pd.to_numeric(frame["open_time"], errors="raise").astype("int64")
    frame["close_time"] = pd.to_numeric(frame["close_time"], errors="raise").astype("int64")
    unit = detect_timestamp_unit(frame["open_time"])
    frame["event_ts"] = pd.to_datetime(frame["open_time"], unit=unit, utc=True)
    frame["close_ts"] = pd.to_datetime(frame["close_time"], unit=unit, utc=True)
    frame["source_timestamp_unit"] = unit
    return frame


def detect_timestamp_unit(values: pd.Series) -> str:
    maximum = int(values.max())
    if maximum >= 10**15:
        return "us"
    if maximum >= 10**12:
        return "ms"
    if maximum >= 10**9:
        return "s"
    raise ValueError("Unsupported Binance timestamp magnitude.")
