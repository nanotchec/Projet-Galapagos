from __future__ import annotations

from pathlib import Path

VERSION = "V2.6"
CORRECTION_VERSION = "V2.6.2"
LABEL_SCHEMA_VERSION = "V2.6"

TARGET_TIMEFRAMES = ["1m", "5m", "15m", "1h"]
HORIZONS = [1, 3, 5]
THRESHOLD = 0.0005

MANIFEST_PATH = Path("reports/manifests/clean_label_factory_v2_6_manifest.json")
QUALITY_JSON_PATH = Path("reports/labels/clean_label_factory_v2_6.json")
QUALITY_MD_PATH = Path("reports/labels/clean_label_factory_v2_6.md")


def get_label_gold_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/gold/labels/forward_returns"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / "year=2024"
        / "month=01"
        / f"labels-2024-01-15.parquet"
    )
