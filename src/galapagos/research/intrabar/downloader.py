"""Intrabar data downloader for research purposes."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

from galapagos.research.intrabar.data_sources import INTRABAR_SCHEMA

logger = logging.getLogger(__name__)


def get_binance_klines(
    symbol: str, interval: str, start_time: int, end_time: int, limit: int = 1000
) -> list[list]:
    """Fetch klines from Binance public API."""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": limit,
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def download_intrabar_sample(
    source: str,
    symbol: str,
    timeframe: str,
    days: int,
    output_dir: str = "data/silver/intrabar",
    dry_run: bool = False,
) -> dict:
    """Download a controlled sample of intrabar data."""
    if source != "binance":
        raise NotImplementedError(f"Download for {source} not yet implemented in V1.18.")

    # Cap days as a safety net to prevent massive downloads
    if timeframe == "1m" and days > 7:
        logger.warning("Capping 1m download to 7 days for safety.")
        days = 7
    elif timeframe == "5m" and days > 30:
        logger.warning("Capping 5m download to 30 days for safety.")
        days = 30

    out_dir = Path(output_dir) / source / symbol / timeframe
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = Path("data/manifests/intrabar")
    manifest_dir.mkdir(parents=True, exist_ok=True)

    file_path = out_dir / "sample.parquet"
    manifest_path = manifest_dir / f"{source}_{symbol}_{timeframe}_manifest.json"

    if dry_run:
        return {
            "status": "dry_run",
            "source": source,
            "symbol": symbol,
            "timeframe": timeframe,
            "days": days,
            "rows": 0,
            "file_path": str(file_path),
        }

    # Fetch slightly older data to match the recent window 2026 if possible?
    # Actually the instruction is just `datetime.now()` minus `days`, but the dataset goes up to April 2026.
    # To have overlapping data with our research dataset, we should align the end date.
    # But since it's "live" API, we can only get up to "now". We will get the last N days.
    # That's fine for the foundation. The orchestrator will try to align what's available.
    end_dt = datetime.now(UTC)
    start_dt = end_dt - timedelta(days=days)

    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)

    all_klines = []
    current_ts = start_ts

    while current_ts < end_ts:
        try:
            klines = get_binance_klines(symbol, timeframe, current_ts, end_ts)
        except Exception as e:
            logger.error(f"Download failed at {current_ts}: {e}")
            break

        if not klines:
            break

        all_klines.extend(klines)
        # last candle open time + 1 ms to avoid duplication
        current_ts = klines[-1][0] + 1
        time.sleep(0.5)  # Rate limit respect

    if not all_klines:
        return {"status": "failed", "reason": "no data returned"}

    # Process into dataframe
    df = pd.DataFrame(
        all_klines,
        columns=[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_volume",
            "trades",
            "taker_base",
            "taker_quote",
            "ignore",
        ],
    )

    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["available_timestamp"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)

    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = df[c].astype(float)

    df["source"] = source
    df["symbol"] = symbol
    df["timeframe"] = timeframe
    df["downloaded_at"] = datetime.now(UTC)

    df = df[INTRABAR_SCHEMA]
    df.sort_values("timestamp", inplace=True)
    df.drop_duplicates(subset=["timestamp"], inplace=True)

    df.to_parquet(file_path, index=False)

    # Hash the file
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    manifest = {
        "source": source,
        "symbol": symbol,
        "timeframe": timeframe,
        "start_time": df["timestamp"].min().isoformat(),
        "end_time": df["timestamp"].max().isoformat(),
        "rows": len(df),
        "file_hash": file_hash,
        "generated_at": datetime.now(UTC).isoformat(),
    }

    manifest_path.write_text(json.dumps(manifest, indent=2))

    return {
        "status": "success",
        "source": source,
        "symbol": symbol,
        "timeframe": timeframe,
        "rows": len(df),
        "file_path": str(file_path),
        "manifest_path": str(manifest_path),
    }
