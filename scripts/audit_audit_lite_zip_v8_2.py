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

from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V8_2


VERSION = "V8.2"
AUDIT_JSON = Path("reports/audit_lite/zip_audit_v8_2.json")
AUDIT_MD = Path("reports/audit_lite/zip_audit_v8_2.md")
REQUIRED_SOURCE_PREFIXES = ["src/galapagos/data/public_trades/"]
REQUIRED_ENTRIES = {
    "README.md",
    "pyproject.toml",
    "reports/data_quality/public_trades_1y_window_v8_2_discovery.json",
    "reports/data_quality/public_trades_1y_window_v8_2_discovery.md",
    "reports/manifests/public_trades_1y_window_v8_2_manifest.json",
    "reports/data_quality/public_trades_1y_window_v8_2.json",
    "reports/data_quality/public_trades_1y_window_v8_2.md",
    "docs/public_trades_1y_window_v8_2.md",
    "reports/audit_lite/v8_2_artifact_inventory.json",
    "reports/audit_lite/v8_2_artifact_inventory.md",
    "reports/audit_lite/v8_2_parquet_summary.json",
    "reports/audit_lite/v8_2_full_local_validation_attestation.json",
    "reports/audit_lite/v8_2_full_local_validation_attestation.md",
    "reports/audit_lite/zip_size_report_v8_2.json",
    "reports/audit_lite/zip_size_report_v8_2.md",
    "reports/PROJECT_STATE.json",
    "reports/PROJECT_STATE.md",
    "reports/current/latest_metrics.json",
    "reports/current/latest_metrics.md",
    "reports/current/latest_summary.md",
    "scripts/discover_public_trades_v8_2.py",
    "scripts/run_public_trades_1y_window_v8_2.py",
    "scripts/validate_public_trades_1y_window_v8_2.py",
    "scripts/release_audit_lite_zip_v8_2.py",
    "scripts/audit_audit_lite_zip_v8_2.py",
    "scripts/smoke_audit_lite_zip_v8_2.py",
    "tests/data/test_public_trades_1y_window_v8_2.py",
    "tests/validation/test_public_trades_1y_window_v8_2_validator.py",
}
SAMPLE_ENTRY = "data/audit_lite/v8_2/trades/sample.parquet"
FORBIDDEN_PREFIXES = (
    "data/raw/",
    "data/research/",
    "reports/backtests/",
    "reports/strategies/",
    "reports/signals/",
    "reports/predictions/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
)
FORBIDDEN_SUFFIXES = (".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pyc", ".zip")
FORBIDDEN_PARTS = ("__pycache__", ".git", ".venv", ".pytest_cache", ".ruff_cache", ".mypy_cache")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    result = audit_zip(Path(args.zip_path).resolve())
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


def audit_zip(zip_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not zip_path.exists():
        return _result(zip_path, 0, [], [f"missing zip: {zip_path}"], warnings)
    try:
        with zipfile.ZipFile(zip_path) as archive:
            bad_member = archive.testzip()
            entries = sorted(archive.namelist())
            top_files = sorted(
                [{"path": item.filename, "bytes": item.file_size} for item in archive.infolist() if not item.is_dir()],
                key=lambda item: item["bytes"],
                reverse=True,
            )[:20]
    except zipfile.BadZipFile as exc:
        return _result(zip_path, zip_path.stat().st_size, [], [f"zip not extractible: {exc}"], warnings)
    if bad_member:
        errors.append(f"zip not extractible: {bad_member}")
    entry_set = set(entries)
    for prefix in REQUIRED_SOURCE_PREFIXES:
        if not any(entry.startswith(prefix) for entry in entries):
            errors.append(f"missing required source package: {prefix}")
    missing = sorted((REQUIRED_ENTRIES | {SAMPLE_ENTRY}) - entry_set)
    errors.extend(f"missing required entry: {entry}" for entry in missing)
    for entry in entries:
        if _is_forbidden_pytest_collectible_script(entry):
            errors.append(f"forbidden pytest-collectible script found: {entry}")
        if _is_forbidden_artifact(entry):
            errors.append(f"forbidden artifact found: {entry}")

    with tempfile.TemporaryDirectory(prefix="galapagos-v8-2-audit-") as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(root)
        manifest = _read_json(root / "reports/manifests/public_trades_1y_window_v8_2_manifest.json")
        report = _read_json(root / "reports/data_quality/public_trades_1y_window_v8_2.json")
        if manifest != report:
            errors.append("V8.2 manifest/report mismatch in ZIP")
        if manifest.get("version") != VERSION or manifest.get("status") != "PASS":
            errors.append("V8.2 manifest version/status mismatch in ZIP")
        safety = manifest.get("safety", {})
        for flag in ["trading_enabled", "orders_enabled", "paper_live_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled", "ml_enabled", "labels_enabled", "dataset_enabled"]:
            if safety.get(flag) is not False:
                errors.append(f"V8.2 safety flag must be false: {flag}")
        sample = root / SAMPLE_ENTRY
        if sample.exists():
            frame = pd.read_parquet(sample, engine="pyarrow")
            if list(frame.columns) != AGG_TRADE_COLUMNS_V8_2:
                errors.append("V8.2 sample schema mismatch")
            if len(frame) == 0:
                errors.append("V8.2 sample must not be empty")
    return _result(zip_path, zip_path.stat().st_size, entries, errors, warnings, top_files=top_files)


def _is_forbidden_pytest_collectible_script(entry: str) -> bool:
    path = Path(entry)
    if len(path.parts) != 2 or path.parts[0] != "scripts" or path.suffix != ".py":
        return False
    return path.name.startswith("test_") or path.name.endswith("_test.py")


def _is_forbidden_artifact(entry: str) -> bool:
    path = Path(entry)
    if any(part in FORBIDDEN_PARTS for part in path.parts):
        return True
    if entry.startswith(FORBIDDEN_PREFIXES):
        return True
    if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return True
    if entry.endswith(".parquet") and entry != SAMPLE_ENTRY:
        return True
    return False


def _result(
    zip_path: Path,
    size: int,
    entries: list[str],
    errors: list[str],
    warnings: list[str],
    *,
    top_files: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "zip_path": str(zip_path),
        "zip_size_bytes": int(size),
        "zip_size_mb": round(size / 1024 / 1024, 3) if size else 0,
        "entries": len(entries),
        "top_20_largest_files": top_files or [],
        "pytest_collectible_scripts_absent": not any(_is_forbidden_pytest_collectible_script(entry) for entry in entries),
        "raw_zips_absent": not any(entry.startswith("data/raw/") for entry in entries),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_reports(result: dict[str, Any]) -> None:
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Audit ZIP V8.2",
        "",
        f"- ZIP : `{result['zip_path']}`.",
        f"- Taille : `{result['zip_size_bytes']}` octets.",
        f"- Entrees : `{result['entries']}`.",
        f"- Scripts pytest collectables absents : `{result['pytest_collectible_scripts_absent']}`.",
        f"- Raw zips absents : `{result['raw_zips_absent']}`.",
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.",
        f"- Erreurs : `{len(result['errors'])}`.",
    ]
    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
