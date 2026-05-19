from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


REQUIRED = [
    "src/galapagos/data/public_market/resampling.py",
    "src/galapagos/validation/resampling.py",
    "scripts/run_ohlcv_resampling_v2_4.py",
    "scripts/validate_ohlcv_resampling_v2_4.py",
    "scripts/release_clean_zip_v2_4_7.py",
    "scripts/audit_clean_zip_v2_4_7.py",
    "scripts/smoke_test_clean_zip_v2_4_7.py",
    "tests/data/test_ohlcv_resampling_v2_4.py",
    "tests/validation/test_ohlcv_resampling_v2_4_validator.py",
    "reports/manifests/public_market_ingestion_v2_3_manifest.json",
    "reports/manifests/ohlcv_resampling_v2_4_manifest.json",
    "reports/data_quality/ohlcv_resampling_v2_4.json",
    "reports/data_quality/ohlcv_resampling_v2_4.md",
    "docs/ohlcv_resampling_v2_4.md",
    "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-15.zip",
    "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/part-2024-01-15.parquet",
    "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/year=2024/month=01/part-2024-01-15.parquet",
    "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/year=2024/month=01/part-2024-01-15.parquet",
    "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/year=2024/month=01/part-2024-01-15.parquet",
    "pyproject.toml",
    "README.md",
]
RAW_ARCHIVE_ENTRY = "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-15.zip"
FORBIDDEN_PARTS = [".git/", ".venv/", "__pycache__/", ".pytest_cache/", ".ruff_cache/", ".mypy_cache/", "node_modules/"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip)
    errors: list[str] = []
    if not zip_path.exists():
        errors.append("zip missing")
        names: list[str] = []
    else:
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
    for required in REQUIRED:
        if required not in names:
            errors.append(f"missing required entry: {required}")
    for forbidden in FORBIDDEN_PARTS:
        if any(forbidden in name for name in names):
            errors.append(f"forbidden entry found: {forbidden}")
    unexpected_zips = [name for name in names if name.endswith(".zip") and name != RAW_ARCHIVE_ENTRY]
    if unexpected_zips:
        errors.append(f"unexpected nested zip found: {unexpected_zips[:5]}")
    payload = {
        "version": "V2.4.7",
        "resampling_artifact_version": "V2.4",
        "zip_path": str(zip_path.resolve()),
        "zip_size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "entries_count": len(names),
        "clean_zip_audit_passed": not errors,
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_audit_v2_4_7.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_audit_v2_4_7.md").write_text(
        "# Audit ZIP V2.4.7\n\n"
        f"- Statut : `{payload['clean_zip_audit_passed']}`\n"
        f"- Erreurs : `{len(errors)}`\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
