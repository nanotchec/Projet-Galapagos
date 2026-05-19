from __future__ import annotations

from pathlib import Path

VERSION = "V2.5"
CORRECTION_VERSION = "V2.5.1"
FEATURE_SCHEMA_VERSION = "V2.5"

TARGET_TIMEFRAMES = ["1m", "5m", "15m", "1h"]

# Default paths
MANIFEST_PATH = Path("reports/manifests/causal_feature_store_v2_5_manifest.json")
QUALITY_JSON_PATH = Path("reports/features/causal_feature_store_v2_5.json")
QUALITY_MD_PATH = Path("reports/features/causal_feature_store_v2_5.md")


def get_feature_gold_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/gold/features/ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / "year=2024"
        / "month=01"
        / f"features-2024-01-15.parquet"
    )
