from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.backtest.timeframe_utils import timeframe_to_timedelta
from galapagos.data.data_normalizer import normalize_ohlcv
from galapagos.data.kraken_collector import KrakenCollector
from galapagos.utils.paths import project_path
from galapagos.utils.time_utils import utc_now_iso


@dataclass(frozen=True)
class HistoricalDataResult:
    data_path: Path
    metadata_path: Path
    metadata: dict[str, Any]


def cache_kraken_ohlcv(
    *,
    symbol: str,
    timeframe: str,
    days: int,
    output_root: Path | None = None,
    collector: KrakenCollector | None = None,
) -> HistoricalDataResult:
    output_root = output_root or project_path("data/silver/ohlcv/kraken")
    symbol_path = symbol.replace("/", "_")
    target_dir = output_root / symbol_path / timeframe
    target_dir.mkdir(parents=True, exist_ok=True)
    limit = _limit_for_days(timeframe, days)
    timeframe_minutes = int(timeframe_to_timedelta(timeframe).total_seconds() / 60)
    requested_limit = int(days * 24 * 60 / timeframe_minutes)
    raw = (collector or KrakenCollector()).fetch_ohlcv(symbol, timeframe, limit=limit)
    data = normalize_ohlcv(raw).sort_values("timestamp").drop_duplicates("timestamp")
    data_hash = _data_hash(data)
    data_path = _write_dataframe(data, target_dir / f"ohlcv_{timeframe}_{days}d")
    approx_actual_days = (
        (len(data) * timeframe_minutes) / (24 * 60) if len(data) else 0.0
    )
    metadata = {
        "source": "kraken_ccxt",
        "symbol": symbol,
        "timeframe": timeframe,
        "requested_days": days,
        "requested_limit": requested_limit,
        "effective_limit": limit,
        "approx_actual_days": approx_actual_days,
        "timeframe_minutes": timeframe_minutes,
        "downloaded_at_utc": utc_now_iso(),
        "rows": int(len(data)),
        "first_timestamp": str(data["timestamp"].iloc[0]) if len(data) else None,
        "last_timestamp": str(data["timestamp"].iloc[-1]) if len(data) else None,
        "actual_days_less_than_requested": approx_actual_days < days,
        "data_hash": data_hash,
        "data_path": str(data_path),
    }
    metadata_path = target_dir / f"metadata_{timeframe}_{days}d.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return HistoricalDataResult(data_path=data_path, metadata_path=metadata_path, metadata=metadata)


def load_historical_ohlcv(path: str | Path) -> pd.DataFrame:
    file_path = Path(path)
    if file_path.suffix == ".parquet":
        return pd.read_parquet(file_path)
    return pd.read_csv(file_path, parse_dates=["timestamp"])


def find_latest_cached_ohlcv(symbol: str, timeframe: str, root: Path | None = None) -> Path | None:
    root = root or project_path("data/silver/ohlcv/kraken")
    directory = root / symbol.replace("/", "_") / timeframe
    if not directory.exists():
        return None
    files = sorted([*directory.glob("*.parquet"), *directory.glob("*.csv")])
    return files[-1] if files else None


def _limit_for_days(timeframe: str, days: int) -> int:
    minutes = int(timeframe_to_timedelta(timeframe).total_seconds() / 60)
    return max(50, min(720, int(days * 24 * 60 / minutes)))


def _write_dataframe(data: pd.DataFrame, base_path: Path) -> Path:
    parquet_path = base_path.with_suffix(".parquet")
    try:
        data.to_parquet(parquet_path, index=False)
        return parquet_path
    except Exception:  # noqa: BLE001
        csv_path = base_path.with_suffix(".csv")
        data.to_csv(csv_path, index=False)
        return csv_path


def _data_hash(data: pd.DataFrame) -> str:
    payload = data.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
