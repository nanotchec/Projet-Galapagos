from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any


VERSION = "V8.9"
AUDIT_JSON = Path("reports/audit_lite/zip_audit_v8_9.json")
AUDIT_MD = Path("reports/audit_lite/zip_audit_v8_9.md")
REQUIRED_ENTRIES = {
    "reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json",
    "reports/features/ohlcv_trades_feature_audit_v8_9.json",
    "reports/features/ohlcv_trades_feature_audit_v8_9.md",
    "reports/features/ohlcv_trades_feature_selection_v8_9.json",
    "reports/features/ohlcv_trades_feature_selection_v8_9.md",
    "reports/audit_lite/v8_9_full_local_validation_attestation.json",
    "reports/audit_lite/v8_9_full_local_validation_attestation.md",
    "reports/audit_lite/v8_9_artifact_inventory.json",
    "reports/audit_lite/v8_9_artifact_inventory.md",
    "reports/audit_lite/zip_size_report_v8_9.json",
    "reports/audit_lite/zip_size_report_v8_9.md",
    "docs/ohlcv_trades_feature_audit_v8_9.md",
    "scripts/run_ohlcv_trades_feature_audit_v8_9.py",
    "scripts/validate_ohlcv_trades_feature_audit_v8_9.py",
    "scripts/release_audit_lite_zip_v8_9.py",
    "scripts/audit_audit_lite_zip_v8_9.py",
    "scripts/smoke_audit_lite_zip_v8_9.py",
    "tests/features/test_ohlcv_trades_feature_audit_v8_9.py",
    "tests/validation/test_ohlcv_trades_feature_audit_v8_9_validator.py",
    "reports/PROJECT_STATE.json",
    "reports/PROJECT_STATE.md",
    "reports/current/latest_metrics.json",
    "reports/current/latest_metrics.md",
    "reports/current/latest_summary.md",
    "README.md",
    "pyproject.toml",
}
REQUIRED_SOURCE_PREFIXES = [
    "src/galapagos/features/",
    "src/galapagos/datasets/",
    "src/galapagos/ml/",
    "src/galapagos/validation/",
]
FORBIDDEN_PREFIXES = (
    "data/raw/",
    "data/research/",
    "reports/backtests/",
    "reports/strategies/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
)
FORBIDDEN_SUFFIXES = (".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pyc", ".zip")
FORBIDDEN_PARTS = ("__pycache__", ".git", ".venv", ".pytest_cache", ".ruff_cache", ".mypy_cache")


def audit_zip(zip_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not zip_path.exists():
        return _result(zip_path, 0, [], [f"missing zip: {zip_path}"], warnings)
    try:
        with zipfile.ZipFile(zip_path) as archive:
            bad_member = archive.testzip()
            entries = sorted(archive.namelist())
    except zipfile.BadZipFile as exc:
        return _result(zip_path, zip_path.stat().st_size, [], [f"zip not extractible: {exc}"], warnings)
    if bad_member:
        errors.append(f"zip not extractible: {bad_member}")
    entry_set = set(entries)
    for entry in sorted(REQUIRED_ENTRIES - entry_set):
        errors.append(f"missing required entry: {entry}")
    for prefix in REQUIRED_SOURCE_PREFIXES:
        if not any(entry.startswith(prefix) for entry in entries):
            errors.append(f"missing required source package: {prefix}")
    for entry in entries:
        if _is_forbidden_artifact(entry):
            errors.append(f"forbidden artifact found: {entry}")
    return _result(zip_path, zip_path.stat().st_size, entries, errors, warnings)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    result = audit_zip(Path(args.zip_path).resolve())
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


def _is_forbidden_artifact(entry: str) -> bool:
    path = Path(entry)
    return any(part in FORBIDDEN_PARTS for part in path.parts) or entry.startswith(FORBIDDEN_PREFIXES) or entry.endswith(FORBIDDEN_SUFFIXES)


def _result(zip_path: Path, size: int, entries: list[str], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "zip_path": str(zip_path),
        "zip_size_bytes": int(size),
        "zip_size_mb": round(size / 1024 / 1024, 3) if size else 0,
        "entries": len(entries),
        "raw_zips_absent": not any(entry.startswith("data/raw/") for entry in entries),
        "full_research_data_absent": not any(entry.startswith("data/research/") for entry in entries),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _write_reports(result: dict[str, Any]) -> None:
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    AUDIT_MD.write_text(
        "\n".join(
            [
                "# Audit ZIP V8.9",
                "",
                f"- ZIP : `{result['zip_path']}`.",
                f"- Taille : `{result['zip_size_bytes']}` octets.",
                f"- Entrees : `{result['entries']}`.",
                f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.",
                f"- Erreurs : `{len(result['errors'])}`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
