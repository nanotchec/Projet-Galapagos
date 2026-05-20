from __future__ import annotations

import json
import zipfile
from pathlib import Path


ZIP_NAME = "projet-galapagos-v3.0-clean.zip"
REPORT_PATH = Path("reports/release_zip_v3_0.json")
REPORT_MD_PATH = Path("reports/release_zip_v3_0.md")

TIMEFRAMES = ["1m", "5m", "15m", "1h"]
DATES = ["2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18", "2024-01-19", "2024-01-20", "2024-01-21"]
DATASET_BASE = "data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT"
ML_BASE = "data/gold/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT"
V2_9_BASE = "data/research/v2_9/silver/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT"
V3_0_BASE = "data/research/v3_0/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT"

INCLUDED_PATHS = [
    "src/galapagos/data/public_market",
    "src/galapagos/validation",
    "src/galapagos/features",
    "src/galapagos/labels",
    "src/galapagos/datasets",
    "src/galapagos/ml",
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
    "scripts/run_offline_ml_research_v2_8.py",
    "scripts/validate_offline_ml_research_v2_8.py",
    "scripts/release_clean_zip_v2_8_1.py",
    "scripts/audit_clean_zip_v2_8_1.py",
    "scripts/smoke_test_clean_zip_v2_8_1.py",
    "scripts/release_clean_zip_v2_8_2.py",
    "scripts/audit_clean_zip_v2_8_2.py",
    "scripts/smoke_test_clean_zip_v2_8_2.py",
    "scripts/release_clean_zip_v2_8_3.py",
    "scripts/audit_clean_zip_v2_8_3.py",
    "scripts/smoke_test_clean_zip_v2_8_3.py",
    "scripts/release_clean_zip_v2_8_4.py",
    "scripts/audit_clean_zip_v2_8_4.py",
    "scripts/smoke_test_clean_zip_v2_8_4.py",
    "scripts/run_multi_day_public_market_data_v2_9.py",
    "scripts/validate_multi_day_public_market_data_v2_9.py",
    "scripts/release_clean_zip_v2_9.py",
    "scripts/audit_clean_zip_v2_9.py",
    "scripts/smoke_test_clean_zip_v2_9.py",
    "scripts/release_clean_zip_v2_9_1.py",
    "scripts/audit_clean_zip_v2_9_1.py",
    "scripts/smoke_test_clean_zip_v2_9_1.py",
    "scripts/run_multi_day_causal_feature_store_v3_0.py",
    "scripts/validate_multi_day_causal_feature_store_v3_0.py",
    "scripts/release_clean_zip_v3_0.py",
    "scripts/audit_clean_zip_v3_0.py",
    "scripts/smoke_test_clean_zip_v3_0.py",
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
    "tests/ml/test_offline_ml_research_v2_8.py",
    "tests/validation/test_offline_ml_research_v2_8_validator.py",
    "tests/data/test_multi_day_public_market_data_v2_9.py",
    "tests/validation/test_multi_day_public_market_data_v2_9_validator.py",
    "tests/features/test_multi_day_causal_features_v3_0.py",
    "tests/validation/test_multi_day_causal_feature_store_v3_0_validator.py",
    "reports/manifests/public_market_ingestion_v2_3_manifest.json",
    "reports/manifests/ohlcv_resampling_v2_4_manifest.json",
    "reports/manifests/causal_feature_store_v2_5_manifest.json",
    "reports/manifests/clean_label_factory_v2_6_manifest.json",
    "reports/manifests/offline_supervised_dataset_v2_7_manifest.json",
    "reports/manifests/offline_ml_research_v2_8_manifest.json",
    "reports/manifests/multi_day_public_market_data_v2_9_manifest.json",
    "reports/manifests/multi_day_causal_feature_store_v3_0_manifest.json",
    "reports/data_quality/public_market_ingestion_v2_3.json",
    "reports/data_quality/public_market_ingestion_v2_3.md",
    "reports/data_quality/ohlcv_resampling_v2_4.json",
    "reports/data_quality/ohlcv_resampling_v2_4.md",
    "reports/data_quality/multi_day_public_market_data_v2_9.json",
    "reports/data_quality/multi_day_public_market_data_v2_9.md",
    "reports/features/causal_feature_store_v2_5.json",
    "reports/features/causal_feature_store_v2_5.md",
    "reports/features/multi_day_causal_feature_store_v3_0.json",
    "reports/features/multi_day_causal_feature_store_v3_0.md",
    "reports/labels/clean_label_factory_v2_6.json",
    "reports/labels/clean_label_factory_v2_6.md",
    "reports/datasets/offline_supervised_dataset_v2_7.json",
    "reports/datasets/offline_supervised_dataset_v2_7.md",
    "reports/datasets/offline_supervised_dataset_v2_7_datacard.md",
    "reports/ml/offline_ml_research_v2_8.json",
    "reports/ml/offline_ml_research_v2_8.md",
    "reports/ml/offline_research_scores_v2_8.json",
    "reports/ml/offline_research_scores_v2_8.md",
    "docs/public_market_ingestion_v2_3.md",
    "docs/ohlcv_resampling_v2_4.md",
    "docs/causal_feature_store_v2_5.md",
    "docs/clean_label_factory_v2_6.md",
    "docs/offline_supervised_dataset_v2_7.md",
    "docs/offline_ml_research_v2_8.md",
    "docs/multi_day_public_market_data_v2_9.md",
    "docs/multi_day_causal_feature_store_v3_0.md",
    "reports/PROJECT_STATE.json",
    "reports/PROJECT_STATE.md",
    "reports/current/latest_metrics.json",
    "reports/current/latest_metrics.md",
    "reports/current/latest_summary.md",
    "reports/REPORT_INDEX.md",
    "pyproject.toml",
    "README.md",
]

for date in DATES:
    INCLUDED_PATHS.append(f"data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-{date}.zip")

for tf in TIMEFRAMES:
    INCLUDED_PATHS.extend(
        [
            f"data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={tf}/year=2024/month=01/part-2024-01-15.parquet",
            f"data/gold/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={tf}/year=2024/month=01/features-2024-01-15.parquet",
            f"data/gold/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={tf}/year=2024/month=01/labels-2024-01-15.parquet",
            f"{DATASET_BASE}/timeframe={tf}/year=2024/month=01/dataset-2024-01-15.parquet",
            f"{DATASET_BASE}/timeframe={tf}/year=2024/month=01/splits-2024-01-15.parquet",
            f"{ML_BASE}/timeframe={tf}/year=2024/month=01/ml-scores-2024-01-15.parquet",
            f"{V2_9_BASE}/timeframe={tf}/window=2024-01-15_2024-01-21/ohlcv.parquet",
            f"{V3_0_BASE}/timeframe={tf}/window=2024-01-15_2024-01-21/features.parquet",
        ]
    )

EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_PREFIXES = [
    "models/",
    "checkpoints/",
    "reports/backtests/",
    "reports/strategies/",
    "reports/signals/",
    "reports/predictions/",
    "orders/",
    "execution/",
    "data/research/v3_0/labels/",
    "data/research/v3_0/datasets/",
    "data/research/v3_0/ml/",
    "data/research/v3_0/backtests/",
]
FORBIDDEN_SUFFIXES = {".pkl", ".pickle", ".joblib", ".sav", ".model", ".ckpt", ".pt", ".pth", ".onnx"}


def main() -> None:
    root = Path(".").resolve()
    zip_path = root / ZIP_NAME
    included = collect_files(root)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in included:
            archive.write(root / relative, relative.as_posix())
    payload = {
        "version": "V3.0",
        "status": "PASS",
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size,
        "files_included": len(included),
        "minimal_clean_zip": True,
        "contains_multi_day_raw": True,
        "contains_multi_day_outputs": True,
        "contains_multi_day_features": True,
        "forbidden_entries_included": False,
        "release_ready_for_external_audit": True,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(
        "# Release ZIP V3.0\n\n"
        f"- Statut : `{payload['status']}`\n"
        f"- ZIP : `{payload['zip_path']}`\n"
        f"- Taille : `{payload['zip_size_bytes']}` octets\n"
        "- Usage : audit externe de la preview feature store causal multi-day V3.0.\n",
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
    if relative.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return False
    if relative.suffix == ".zip" and not name.startswith("data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/"):
        return False
    return not any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)


if __name__ == "__main__":
    main()
