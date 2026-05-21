from __future__ import annotations

from pathlib import Path

from galapagos.data.public_market.multi_day import WINDOW_LABEL


VERSION = "V3.1"
LABEL_SCHEMA_VERSION = "V3.1"
TIMEFRAMES_V3_1 = ["1m", "5m", "15m", "1h"]
MANIFEST_PATH = Path("reports/manifests/multi_day_label_factory_v3_1_manifest.json")
REPORT_JSON_PATH = Path("reports/labels/multi_day_label_factory_v3_1.json")
REPORT_MD_PATH = Path("reports/labels/multi_day_label_factory_v3_1.md")
DOC_PATH = Path("docs/multi_day_label_factory_v3_1.md")
EXPECTED_LIMITATIONS_V3_1 = [
    "V3.1 produit uniquement des labels forward multi-day separes sur BTCUSDT 2024-01-15 a 2024-01-21 a partir des donnees OHLCV V2.9 validees.",
    "V3.1 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
]


def output_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_1/labels/forward_returns"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_LABEL}"
        / "labels.parquet"
    )
