from __future__ import annotations

import json
import zipfile
from pathlib import Path


ZIP_NAME = "projet-galapagos-v2.7.1-clean.zip"
REPORT_PATH = Path("reports/release_zip_v2_7_1.json")
REPORT_MD_PATH = Path("reports/release_zip_v2_7_1.md")
RAW_ARCHIVE_ENTRY = "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-15.zip"

TIMEFRAMES = ["1m", "5m", "15m", "1h"]
DATASET_BASE = "data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT"

INCLUDED_PATHS = [
    "src/galapagos/data/public_market",
    "src/galapagos/validation",
    "src/galapagos/features",
    "src/galapagos/labels",
    "src/galapagos/datasets",
    "scripts/_bootstrap.py",
    "scripts/run_public_market_ingestion_preview_v2_3.py",
    "scripts/validate_public_market_ingestion_v2_3.py",
    "scripts/run_ohlcv_resampling_v2_4.py",
    "scripts/validate_ohlcv_resampling_v2_4.py",
    "scripts/run_causal_feature_store_v2_5.py",
    "scripts/validate_causal_feature_store_v2_5.py",
    "scripts/run_clean_label_factory_v2_6.py",
    "scripts/validate_clean_label_factory_v2_6.py",
    "scripts/run_offline_supervised_dataset_v2_7.py",
    "scripts/validate_offline_supervised_dataset_v2_7.py",
    "scripts/release_clean_zip_v2_7_1.py",
    "scripts/audit_clean_zip_v2_7_1.py",
    "scripts/smoke_test_clean_zip_v2_7_1.py",
    "tests/data/test_public_market_ingestion_v2_3.py",
    "tests/validation/test_public_market_ingestion_v2_3_validator.py",
    "tests/data/test_ohlcv_resampling_v2_4.py",
    "tests/validation/test_ohlcv_resampling_v2_4_validator.py",
    "tests/features/test_causal_ohlcv_features_v2_5.py",
    "tests/validation/test_causal_feature_store_v2_5_validator.py",
    "tests/labels/test_forward_labels_v2_6.py",
    "tests/validation/test_clean_label_factory_v2_6_validator.py",
    "tests/datasets/test_offline_supervised_dataset_v2_7.py",
    "tests/validation/test_offline_supervised_dataset_v2_7_validator.py",
    "reports/manifests/public_market_ingestion_v2_3_manifest.json",
    "reports/manifests/ohlcv_resampling_v2_4_manifest.json",
    "reports/manifests/causal_feature_store_v2_5_manifest.json",
    "reports/manifests/clean_label_factory_v2_6_manifest.json",
    "reports/manifests/offline_supervised_dataset_v2_7_manifest.json",
    "reports/data_quality/public_market_ingestion_v2_3.json",
    "reports/data_quality/public_market_ingestion_v2_3.md",
    "reports/data_quality/ohlcv_resampling_v2_4.json",
    "reports/data_quality/ohlcv_resampling_v2_4.md",
    "reports/features/causal_feature_store_v2_5.json",
    "reports/features/causal_feature_store_v2_5.md",
    "reports/labels/clean_label_factory_v2_6.json",
    "reports/labels/clean_label_factory_v2_6.md",
    "reports/datasets/offline_supervised_dataset_v2_7.json",
    "reports/datasets/offline_supervised_dataset_v2_7.md",
    "reports/datasets/offline_supervised_dataset_v2_7_datacard.md",
    "docs/public_market_ingestion_v2_3.md",
    "docs/ohlcv_resampling_v2_4.md",
    "docs/causal_feature_store_v2_5.md",
    "docs/clean_label_factory_v2_6.md",
    "docs/offline_supervised_dataset_v2_7.md",
    "reports/PROJECT_STATE.json",
    "reports/PROJECT_STATE.md",
    "reports/current/latest_metrics.json",
    "reports/current/latest_metrics.md",
    "reports/current/latest_summary.md",
    "reports/REPORT_INDEX.md",
    RAW_ARCHIVE_ENTRY,
    "pyproject.toml",
    "README.md",
]

for tf in TIMEFRAMES:
    INCLUDED_PATHS.extend(
        [
            f"data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={tf}/year=2024/month=01/part-2024-01-15.parquet",
            f"data/gold/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={tf}/year=2024/month=01/features-2024-01-15.parquet",
            f"data/gold/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={tf}/year=2024/month=01/labels-2024-01-15.parquet",
            f"{DATASET_BASE}/timeframe={tf}/year=2024/month=01/dataset-2024-01-15.parquet",
            f"{DATASET_BASE}/timeframe={tf}/year=2024/month=01/splits-2024-01-15.parquet",
        ]
    )

EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_ZIP_PREFIXES = ["models/", "reports/ml/", "reports/backtests/", "reports/strategies/", "reports/signals/", "reports/predictions/", "orders/", "execution/"]


def main() -> None:
    root = Path(".").resolve()
    zip_path = root / ZIP_NAME
    included = collect_files(root)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in included:
            archive.write(root / relative, relative.as_posix())

    payload = {
        "version": "V2.7.1",
        "status": "PASS",
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size,
        "files_included": len(included),
        "minimal_clean_zip": True,
        "contains_datasets_gold_parquet": True,
        "contains_split_parquet": True,
        "contains_dataset_validator": True,
        "forbidden_entries_included": False,
        "release_ready_for_external_audit": True,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(
        "# Release ZIP V2.7.1\n\n"
        f"- Statut : `{payload['status']}`\n"
        f"- ZIP : `{payload['zip_path']}`\n"
        f"- Taille : `{payload['zip_size_bytes']}` octets\n"
        "- Usage : audit externe du dataset supervise offline V2.7.1.\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def collect_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for item in INCLUDED_PATHS:
        path = root / item
        if not path.exists():
            raise FileNotFoundError(f"missing release input: {item}")
        if path.is_file():
            if _allowed(path.relative_to(root)):
                files.append(path.relative_to(root))
        else:
            for child in sorted(path.rglob("*")):
                if child.is_file() and _allowed(child.relative_to(root)):
                    files.append(child.relative_to(root))
    return sorted(set(files))


def _allowed(relative: Path) -> bool:
    name = relative.as_posix()
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if relative.name in {".DS_Store", ".env"}:
        return False
    if relative.suffix == ".zip" and name != RAW_ARCHIVE_ENTRY:
        return False
    return not any(name.startswith(prefix) for prefix in FORBIDDEN_ZIP_PREFIXES)


if __name__ == "__main__":
    main()
