from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CcxtFetchPlan:
    exchange: str
    symbol: str
    timeframe: str
    since_iso: str
    until_iso: str
    estimated_pages: int
    output_path: str
    dry_run: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def plan_ccxt_ohlcv_fetch(
    *,
    exchange: str,
    symbol: str,
    timeframe: str,
    years: int,
    max_pages: int = 1000,
    dry_run: bool = True,
) -> CcxtFetchPlan:
    until = datetime.now(UTC)
    since = until - timedelta(days=365 * years)
    interval_minutes = _timeframe_minutes(timeframe)
    estimated_bars = int((until - since).total_seconds() / 60 / interval_minutes)
    estimated_pages = min(max_pages, max(1, estimated_bars // 1000 + 1))
    safe_symbol = symbol.replace("/", "_").replace(":", "_")
    output_path = Path("data/silver/ohlcv/ccxt") / exchange / safe_symbol / timeframe / "ohlcv.csv"
    return CcxtFetchPlan(
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        since_iso=since.isoformat(),
        until_iso=until.isoformat(),
        estimated_pages=estimated_pages,
        output_path=str(output_path),
        dry_run=dry_run,
    )


def _timeframe_minutes(timeframe: str) -> int:
    if timeframe.endswith("m"):
        return int(timeframe[:-1])
    if timeframe.endswith("h"):
        return int(timeframe[:-1]) * 60
    if timeframe.endswith("d"):
        return int(timeframe[:-1]) * 1440
    raise ValueError("Unsupported timeframe.")
