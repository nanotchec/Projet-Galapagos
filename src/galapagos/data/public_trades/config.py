from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


VERSION_V7_0 = "V7.0"
SCHEMA_VERSION_V7_0 = "AGG_TRADE_COLUMNS_V7_0"
BINANCE_PUBLIC_HOST = "data.binance.vision"
ALLOWED_PUBLIC_HOSTS = {BINANCE_PUBLIC_HOST}
SOURCE_NAME = "binance_archive"
SOURCE_DISPLAY_NAME = "binance_public_archive"
VENUE = "binance"
MARKET_TYPE = "spot"
SYMBOL = "BTCUSDT"
TRADE_SOURCE_TYPE = "aggTrades"
DEFAULT_PREVIEW_DAYS = 1
V5_0_MANIFEST_PATH = Path("reports/manifests/max_history_public_market_data_v5_0_manifest.json")
DISCOVERY_JSON_PATH_V7_0 = Path("reports/data_quality/public_trades_v7_0_discovery.json")
DISCOVERY_MD_PATH_V7_0 = Path("reports/data_quality/public_trades_v7_0_discovery.md")
MANIFEST_PATH_V7_0 = Path("reports/manifests/public_trades_v7_0_manifest.json")
REPORT_JSON_PATH_V7_0 = Path("reports/data_quality/public_trades_v7_0.json")
REPORT_MD_PATH_V7_0 = Path("reports/data_quality/public_trades_v7_0.md")
DOC_PATH_V7_0 = Path("docs/public_trades_ingestion_v7_0.md")
LIMITATIONS_V7_0 = [
    "V7.0 ingere uniquement des trades publics historiques en lecture seule.",
    "V7.0 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.",
]


@dataclass(frozen=True)
class PublicTradesWindow:
    window_start: str
    window_end: str
    total_days: int
    matches_v5_0_window: bool
    reason: str


def raw_zip_path(root: Path, date: str, trade_source_type: str = TRADE_SOURCE_TYPE) -> Path:
    return (
        root
        / "data/raw/public_trades/binance_archive/spot/BTCUSDT"
        / trade_source_type
        / f"BTCUSDT-{trade_source_type}-{date}.zip"
    )


def output_path(root: Path, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v7_0/trades/aggTrades"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"window={window_start}_{window_end}"
        / "agg_trades.parquet"
    )
