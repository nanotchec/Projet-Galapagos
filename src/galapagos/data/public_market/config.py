from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


VERSION = "V2.3"
VERSION_SUFFIX = "v2_3"
MISSION = "Public Market Data Read-Only Ingestion Preview"
BINANCE_PUBLIC_HOST = "data.binance.vision"
ALLOWED_PUBLIC_HOSTS = {BINANCE_PUBLIC_HOST}
EXPECTED_ROWS_BY_TIMEFRAME = {"1m": 1440}


@dataclass(frozen=True)
class PublicMarketIngestionConfig:
    source: str
    market_type: str
    symbol: str
    timeframe: str
    date: str
    output_root: Path = Path(".")
    force: bool = False
    no_network: bool = False
    fail_on_quality_warning: bool = False

    def validate(self) -> None:
        if self.source != "binance_archive":
            raise ValueError("V2.3 supports source=binance_archive only.")
        if self.market_type != "spot":
            raise ValueError("V2.3 supports market_type=spot only.")
        if self.symbol != "BTCUSDT":
            raise ValueError("V2.3 supports symbol=BTCUSDT only.")
        if self.timeframe != "1m":
            raise ValueError("V2.3 supports timeframe=1m only.")
        if self.date != "2024-01-15":
            raise ValueError("V2.3 uses fixed date 2024-01-15 only.")

    @property
    def expected_rows(self) -> int:
        return EXPECTED_ROWS_BY_TIMEFRAME[self.timeframe]

    @property
    def raw_path(self) -> Path:
        return (
            self.output_root
            / "data/raw/public_market/binance_archive"
            / self.market_type
            / self.symbol
            / "klines"
            / self.timeframe
            / f"{self.symbol}-{self.timeframe}-{self.date}.zip"
        )

    @property
    def silver_path(self) -> Path:
        year, month, _day = self.date.split("-")
        return (
            self.output_root
            / "data/silver/market_data/ohlcv"
            / "source=binance_archive"
            / f"market_type={self.market_type}"
            / f"symbol={self.symbol}"
            / f"timeframe={self.timeframe}"
            / f"year={year}"
            / f"month={month}"
            / f"part-{self.date}.parquet"
        )

    @property
    def manifest_path(self) -> Path:
        return self.output_root / "reports/manifests/public_market_ingestion_v2_3_manifest.json"

    @property
    def quality_json_path(self) -> Path:
        return self.output_root / "reports/data_quality/public_market_ingestion_v2_3.json"

    @property
    def quality_md_path(self) -> Path:
        return self.output_root / "reports/data_quality/public_market_ingestion_v2_3.md"
