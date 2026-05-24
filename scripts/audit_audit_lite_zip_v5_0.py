from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.schemas import OHLCV_COLUMNS


VERSION = "V5.0"
REPORT_JSON = Path("reports/audit_lite/zip_audit_v5_0.json")
REPORT_MD = Path("reports/audit_lite/zip_audit_v5_0.md")
REQUIRED_FILES = {
    "README.md",
    "pyproject.toml",
    "reports/manifests/max_history_public_market_data_v5_0_manifest.json",
    "reports/data_quality/max_history_public_market_data_v5_0.json",
    "reports/data_quality/max_history_public_market_data_v5_0.md",
    "reports/data_quality/max_history_public_market_data_v5_0_discovery.json",
    "reports/data_quality/max_history_public_market_data_v5_0_discovery.md",
    "reports/audit_lite/v5_0_artifact_inventory.json",
    "reports/audit_lite/v5_0_artifact_inventory.md",
    "reports/audit_lite/v5_0_parquet_summary.json",
    "reports/audit_lite/v5_0_full_local_validation_attestation.json",
    "reports/audit_lite/v5_0_full_local_validation_attestation.md",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_summary.md",
    "docs/max_history_public_market_data_v5_0.md",
    "scripts/discover_max_history_public_market_data_v5_0.py",
    "scripts/run_max_history_public_market_data_v5_0.py",
    "scripts/validate_max_history_public_market_data_v5_0.py",
    "scripts/release_audit_lite_zip_v5_0.py",
    "scripts/audit_audit_lite_zip_v5_0.py",
    "scripts/smoke_audit_lite_zip_v5_0.py",
    "tests/data/test_max_history_public_market_data_v5_0.py",
    "tests/validation/test_max_history_public_market_data_v5_0_validator.py",
}
REQUIRED_DIR_PREFIXES = [
    "src/galapagos/data/public_market/",
    "src/galapagos/validation/",
]
REQUIRED_SAMPLES = {
    "data/audit_lite/v5_0/ohlcv/timeframe=1m/sample.parquet",
    "data/audit_lite/v5_0/ohlcv/timeframe=5m/sample.parquet",
    "data/audit_lite/v5_0/ohlcv/timeframe=15m/sample.parquet",
    "data/audit_lite/v5_0/ohlcv/timeframe=1h/sample.parquet",
}
FORBIDDEN_PREFIXES = [
    "data/raw/public_market/",
    "data/research/",
    "reports/backtests/",
    "reports/strategies/",
    "reports/signals/",
    "reports/predictions/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
]
FORBIDDEN_SUFFIXES = {".zip", ".pyc", ".pyo", ".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    result = audit_zip(Path(args.zip_path).resolve())
    _write_json(REPORT_JSON, result)
    _write_text(REPORT_MD, _render_markdown(result))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


def audit_zip(zip_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    entries: list[str] = []
    top_files: list[dict[str, Any]] = []
    if not zip_path.exists():
        return _result(zip_path, [f"missing ZIP: {zip_path}"], warnings, entries, top_files)
    try:
        with zipfile.ZipFile(zip_path) as archive:
            entries = sorted(archive.namelist())
            top_files = sorted(
                ({"path": item.filename, "bytes": item.file_size} for item in archive.infolist() if not item.is_dir()),
                key=lambda item: item["bytes"],
                reverse=True,
            )[:20]
            archive.testzip()
    except zipfile.BadZipFile as exc:
        return _result(zip_path, [f"invalid ZIP: {exc}"], warnings, entries, top_files)

    entry_set = set(entries)
    missing = sorted((REQUIRED_FILES | REQUIRED_SAMPLES) - entry_set)
    if missing:
        errors.append(f"missing required audit-lite files: {missing}")
    for prefix in REQUIRED_DIR_PREFIXES:
        if not any(entry.startswith(prefix) for entry in entries):
            errors.append(f"missing required source package: {prefix}")
    for entry in entries:
        path = Path(entry)
        if "__pycache__" in path.parts or path.suffix.casefold() in {".pyc", ".pyo"}:
            errors.append(f"forbidden Python cache found: {entry}")
        if any(entry.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            errors.append(f"forbidden path in audit-lite ZIP: {entry}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden suffix in audit-lite ZIP: {entry}")
        if path.suffix.casefold() == ".parquet" and entry not in REQUIRED_SAMPLES:
            errors.append(f"unexpected Parquet in audit-lite ZIP: {entry}")

    with tempfile.TemporaryDirectory(prefix="galapagos-v5-0-audit-") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
        manifest = _read_json(extract_root / "reports/manifests/max_history_public_market_data_v5_0_manifest.json")
        report = _read_json(extract_root / "reports/data_quality/max_history_public_market_data_v5_0.json")
        discovery = _read_json(extract_root / "reports/data_quality/max_history_public_market_data_v5_0_discovery.json")
        inventory = _read_json(extract_root / "reports/audit_lite/v5_0_artifact_inventory.json")
        attestation = _read_json(extract_root / "reports/audit_lite/v5_0_full_local_validation_attestation.json")
        if manifest != report:
            errors.append("V5.0 manifest/report mismatch in ZIP")
        if manifest.get("version") != VERSION:
            errors.append("V5.0 manifest version mismatch in ZIP")
        if discovery.get("window_start") != manifest.get("discovery", {}).get("window_start"):
            errors.append("V5.0 discovery window_start mismatch in ZIP")
        if len(inventory.get("raw_files_excluded", [])) != manifest.get("discovery", {}).get("expected_raw_files"):
            errors.append("V5.0 raw inventory count must match expected_raw_files")
        if not inventory.get("audit_lite_does_not_replace_full_validation"):
            errors.append("audit-lite must not claim to replace full validation")
        for sample in REQUIRED_SAMPLES:
            frame = pd.read_parquet(extract_root / sample, engine="pyarrow")
            if list(frame.columns) != OHLCV_COLUMNS:
                errors.append(f"sample schema mismatch: {sample}")
        for flag in ["validator_passed", "tests_passed", "audit_lite_passed", "smoke_audit_lite_passed", "no_trading", "no_backtest", "no_orders"]:
            if attestation.get(flag) is not True:
                errors.append(f"V5.0 attestation flag must be true: {flag}")
    return _result(zip_path, errors, warnings, entries, top_files)


def _result(zip_path: Path, errors: list[str], warnings: list[str], entries: list[str], top_files: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "zip_size_mb": round(zip_path.stat().st_size / 1024 / 1024, 3) if zip_path.exists() else 0.0,
        "entries": len(entries),
        "top_20_largest_files": top_files,
        "raw_zips_absent": not any(entry.endswith(".zip") or entry.startswith("data/raw/public_market/") for entry in entries),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _render_markdown(result: dict[str, Any]) -> str:
    status = "PASS" if result["passed"] else "FAIL"
    top = "\n".join(f"- `{item['path']}` : {item['bytes']} octets" for item in result["top_20_largest_files"])
    errors = "\n".join(f"- {error}" for error in result["errors"]) or "- Aucune"
    return f"""# Audit ZIP audit-lite V5.0

- Statut : `{status}`
- ZIP : `{result['zip_path']}`
- Taille : `{result['zip_size_bytes']}` octets
- Raw zips absents : `{result['raw_zips_absent']}`

## Top fichiers

{top}

## Erreurs

{errors}
"""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
