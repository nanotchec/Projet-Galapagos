from __future__ import annotations

import json
import zipfile
from datetime import date, timedelta
from pathlib import Path


VERSION = "V3.5.2"
ZIP_NAME = "projet-galapagos-v3.5.2-clean.zip"
REPORT_PATH = Path("reports/release_zip_v3_5_2.json")
REPORT_MD_PATH = Path("reports/release_zip_v3_5_2.md")
TIMEFRAMES = ["1m", "5m", "15m", "1h"]
DATES = [
    (date.fromisoformat("2024-01-01") + timedelta(days=offset)).isoformat()
    for offset in range((date.fromisoformat("2024-03-30") - date.fromisoformat("2024-01-01")).days + 1)
]
V3_5_BASE = "data/research/v3_5/silver/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT"

INCLUDED_PATHS = [
    "src/galapagos/data/public_market",
    "src/galapagos/validation",
    "src/galapagos/features",
    "src/galapagos/labels",
    "src/galapagos/datasets",
    "src/galapagos/ml",
    "scripts",
    "tests/data",
    "tests/validation",
    "reports/manifests",
    "reports/data_quality",
    "docs",
    "reports/PROJECT_STATE.json",
    "reports/PROJECT_STATE.md",
    "reports/current/latest_metrics.json",
    "reports/current/latest_metrics.md",
    "reports/current/latest_summary.md",
    "reports/REPORT_INDEX.md",
    "galapagos/__init__.py",
    "pyproject.toml",
    "README.md",
]
for current_date in DATES:
    INCLUDED_PATHS.append(f"data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-{current_date}.zip")
for timeframe in TIMEFRAMES:
    INCLUDED_PATHS.append(f"{V3_5_BASE}/timeframe={timeframe}/window=2024-01-01_2024-03-30/ohlcv.parquet")

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
    "data/research/v3_5/features/",
    "data/research/v3_5/labels/",
    "data/research/v3_5/datasets/",
    "data/research/v3_5/ml/",
    "data/research/v3_5/backtests/",
    "data/research/v3_5/strategies/",
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
        "version": VERSION,
        "status": "PASS",
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size,
        "files_included": len(included),
        "contains_90_day_raw": True,
        "contains_v3_5_outputs": True,
        "forbidden_entries_included": False,
        "release_ready_for_external_audit": True,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(
        "# Release ZIP V3.5.2\n\n"
        f"- Statut : `{payload['status']}`\n"
        f"- ZIP : `{payload['zip_path']}`\n"
        f"- Taille : `{payload['zip_size_bytes']}` octets\n"
        "- Usage : audit externe expansion data publique 90 jours V3.5.2.\n",
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
    if relative.name.startswith(".smoke-") or relative.name in {".DS_Store", ".env"}:
        return False
    if "secret" in name.casefold():
        return False
    if relative.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return False
    if relative.suffix == ".zip" and not name.startswith("data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/"):
        return False
    return not any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)


if __name__ == "__main__":
    main()
