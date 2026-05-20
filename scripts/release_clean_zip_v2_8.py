from __future__ import annotations

import json
import zipfile
from pathlib import Path

from release_clean_zip_v2_7_2 import INCLUDED_PATHS as V2_7_INCLUDED_PATHS
from release_clean_zip_v2_7_2 import RAW_ARCHIVE_ENTRY


ZIP_NAME = "projet-galapagos-v2.8-clean.zip"
REPORT_PATH = Path("reports/release_zip_v2_8.json")
REPORT_MD_PATH = Path("reports/release_zip_v2_8.md")
TIMEFRAMES = ["1m", "5m", "15m", "1h"]
ML_BASE = "data/gold/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT"

REMOVED_V2_7_RELEASE_SCRIPTS = {
    "scripts/release_clean_zip_v2_7_2.py",
    "scripts/audit_clean_zip_v2_7_2.py",
    "scripts/smoke_test_clean_zip_v2_7_2.py",
}

V2_8_PATHS = [
    "src/galapagos/ml",
    "scripts/run_offline_ml_research_v2_8.py",
    "scripts/validate_offline_ml_research_v2_8.py",
    "scripts/release_clean_zip_v2_8.py",
    "scripts/audit_clean_zip_v2_8.py",
    "scripts/smoke_test_clean_zip_v2_8.py",
    "tests/ml/test_offline_ml_research_v2_8.py",
    "tests/validation/test_offline_ml_research_v2_8_validator.py",
    "reports/manifests/offline_ml_research_v2_8_manifest.json",
    "reports/ml/offline_ml_research_v2_8.json",
    "reports/ml/offline_ml_research_v2_8.md",
    "reports/ml/offline_research_scores_v2_8.json",
    "reports/ml/offline_research_scores_v2_8.md",
    "docs/offline_ml_research_v2_8.md",
]

INCLUDED_PATHS = [path for path in V2_7_INCLUDED_PATHS if path not in REMOVED_V2_7_RELEASE_SCRIPTS] + V2_8_PATHS
for tf in TIMEFRAMES:
    INCLUDED_PATHS.append(f"{ML_BASE}/timeframe={tf}/year=2024/month=01/ml-scores-2024-01-15.parquet")

EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_ZIP_PREFIXES = [
    "models/",
    "reports/backtests/",
    "reports/strategies/",
    "reports/signals/",
    "reports/predictions/",
    "orders/",
    "execution/",
]


def main() -> None:
    root = Path(".").resolve()
    zip_path = root / ZIP_NAME
    included = collect_files(root)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in included:
            archive.write(root / relative, relative.as_posix())

    payload = {
        "version": "V2.8",
        "status": "PASS",
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size,
        "files_included": len(included),
        "minimal_clean_zip": True,
        "contains_offline_ml_scores": True,
        "contains_offline_ml_validator": True,
        "forbidden_entries_included": False,
        "release_ready_for_external_audit": True,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(
        "# Release ZIP V2.8\n\n"
        f"- Statut : `{payload['status']}`\n"
        f"- ZIP : `{payload['zip_path']}`\n"
        f"- Taille : `{payload['zip_size_bytes']}` octets\n"
        "- Usage : audit externe du laboratoire ML offline V2.8.\n",
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
