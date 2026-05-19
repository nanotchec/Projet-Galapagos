from __future__ import annotations

import json
import zipfile
from pathlib import Path


ZIP_NAME = "projet-galapagos-v2.4.4-clean.zip"
REPORT_PATH = Path("reports/release_zip_v2_4_4.json")
REPORT_MD_PATH = Path("reports/release_zip_v2_4_4.md")
RAW_ARCHIVE_ENTRY = "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-15.zip"

INCLUDED_PATHS = [
    "src/galapagos/data/public_market",
    "src/galapagos/validation",
    "scripts/_bootstrap.py",
    "scripts/run_public_market_ingestion_preview_v2_3.py",
    "scripts/validate_public_market_ingestion_v2_3.py",
    "scripts/run_ohlcv_resampling_v2_4.py",
    "scripts/validate_ohlcv_resampling_v2_4.py",
    "scripts/release_clean_zip_v2_4_4.py",
    "scripts/audit_clean_zip_v2_4_4.py",
    "scripts/smoke_test_clean_zip_v2_4_4.py",
    "tests/data/test_public_market_ingestion_v2_3.py",
    "tests/validation/test_public_market_ingestion_v2_3_validator.py",
    "tests/data/test_ohlcv_resampling_v2_4.py",
    "tests/validation/test_ohlcv_resampling_v2_4_validator.py",
    "reports/manifests/public_market_ingestion_v2_3_manifest.json",
    "reports/manifests/ohlcv_resampling_v2_4_manifest.json",
    "reports/data_quality/public_market_ingestion_v2_3.json",
    "reports/data_quality/public_market_ingestion_v2_3.md",
    "reports/data_quality/ohlcv_resampling_v2_4.json",
    "reports/data_quality/ohlcv_resampling_v2_4.md",
    "docs/public_market_ingestion_v2_3.md",
    "docs/ohlcv_resampling_v2_4.md",
    "reports/PROJECT_STATE.json",
    "reports/PROJECT_STATE.md",
    "reports/current/latest_metrics.json",
    "reports/current/latest_metrics.md",
    "reports/current/latest_summary.md",
    "reports/REPORT_INDEX.md",
    "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-15.zip",
    "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/part-2024-01-15.parquet",
    "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/year=2024/month=01/part-2024-01-15.parquet",
    "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/year=2024/month=01/part-2024-01-15.parquet",
    "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/year=2024/month=01/part-2024-01-15.parquet",
    "pyproject.toml",
    "README.md",
]

EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}


def main() -> None:
    root = Path(".").resolve()
    zip_path = root / ZIP_NAME
    included = collect_files(root)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in included:
            archive.write(root / relative, relative.as_posix())
    payload = {
        "version": "V2.4.4",
        "resampling_artifact_version": "V2.4",
        "status": "PASS",
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size,
        "files_included": len(included),
        "minimal_clean_zip": True,
        "contains_raw_public_archive": True,
        "contains_1m_silver": True,
        "contains_5m_15m_1h_silver": True,
        "contains_resampling_validator": True,
        "contains_tests": True,
        "forbidden_entries_included": False,
        "release_ready_for_external_audit": True,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(
        "# Release ZIP V2.4.4\n\n"
        f"- Statut : `{payload['status']}`\n"
        f"- ZIP : `{payload['zip_path']}`\n"
        f"- Taille : `{payload['zip_size_bytes']}` octets\n"
        "- Usage : audit externe du durcissement manifest/report V2.4.4.\n",
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
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if relative.name in {".DS_Store", ".env"}:
        return False
    if relative.suffix == ".zip" and relative.as_posix() != RAW_ARCHIVE_ENTRY:
        return False
    return True


if __name__ == "__main__":
    main()
