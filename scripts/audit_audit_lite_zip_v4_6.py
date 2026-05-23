from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.storage import read_parquet
from galapagos.ml.schemas import ML_SCORE_COLUMNS_V4_6


VERSION = "V4.6"
REPORT_JSON = Path("reports/audit_lite/zip_audit_v4_6.json")
REPORT_MD = Path("reports/audit_lite/zip_audit_v4_6.md")
REQUIRED_FILES = {
    "README.md",
    "pyproject.toml",
    "reports/manifests/one_year_offline_ml_research_v4_6_manifest.json",
    "reports/ml/one_year_offline_ml_research_v4_6.json",
    "reports/ml/one_year_offline_ml_research_v4_6.md",
    "reports/ml/one_year_offline_research_scores_v4_6.json",
    "reports/ml/one_year_offline_research_scores_v4_6.md",
    "reports/audit_lite/v4_6_artifact_inventory.json",
    "reports/audit_lite/v4_6_artifact_inventory.md",
    "reports/audit_lite/v4_6_parquet_summary.json",
    "reports/audit_lite/v4_6_full_local_validation_attestation.json",
    "reports/audit_lite/v4_6_full_local_validation_attestation.md",
    "reports/audit_lite/zip_size_report_v4_6.json",
    "reports/audit_lite/zip_size_report_v4_6.md",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_summary.md",
    "docs/one_year_offline_ml_research_v4_6.md",
    "scripts/run_one_year_offline_ml_research_v4_6.py",
    "scripts/validate_one_year_offline_ml_research_v4_6.py",
    "scripts/release_audit_lite_zip_v4_6.py",
    "scripts/audit_audit_lite_zip_v4_6.py",
    "scripts/smoke_audit_lite_zip_v4_6.py",
    "tests/ml/test_one_year_offline_ml_research_v4_6.py",
    "tests/validation/test_one_year_offline_ml_research_v4_6_validator.py",
}
REQUIRED_DIR_PREFIXES = [
    "src/galapagos/data/public_market/",
    "src/galapagos/validation/",
    "src/galapagos/features/",
    "src/galapagos/labels/",
    "src/galapagos/datasets/",
    "src/galapagos/ml/",
]
FORBIDDEN_PREFIXES = [
    "data/raw/public_market/",
    "reports/backtests/",
    "reports/strategies/",
    "reports/signals/",
    "reports/predictions/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
    "data/research/v4_6/backtests/",
    "data/research/v4_6/strategies/",
    "data/research/v4_6/orders/",
    "data/research/v4_6/execution/",
    "data/research/v4_6/models/",
    "data/research/v4_6/checkpoints/",
]
REQUIRED_SCORE_SAMPLES = {
    "data/audit_lite/v4_6/ml_scores/timeframe=1m/sample.parquet",
    "data/audit_lite/v4_6/ml_scores/timeframe=5m/sample.parquet",
    "data/audit_lite/v4_6/ml_scores/timeframe=15m/sample.parquet",
    "data/audit_lite/v4_6/ml_scores/timeframe=1h/sample.parquet",
}
FORBIDDEN_SUFFIXES = {".zip", ".pyc", ".pyo", ".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    zip_path = Path(args.zip_path).resolve()
    result = audit_zip(zip_path)
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
    missing = sorted((REQUIRED_FILES | REQUIRED_SCORE_SAMPLES) - entry_set)
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
        if path.suffix.casefold() == ".parquet" and entry not in REQUIRED_SCORE_SAMPLES:
            errors.append(f"unexpected Parquet in audit-lite ZIP: {entry}")
    with tempfile.TemporaryDirectory(prefix="galapagos-v4-6-audit-") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
        for sample in sorted(REQUIRED_SCORE_SAMPLES):
            frame = read_parquet(extract_root / sample)
            if list(frame.columns) != ML_SCORE_COLUMNS_V4_6:
                errors.append(f"sample schema mismatch: {sample}")
        manifest = _read_json(extract_root / "reports/manifests/one_year_offline_ml_research_v4_6_manifest.json")
        scores_report = _read_json(extract_root / "reports/ml/one_year_offline_research_scores_v4_6.json")
        attestation = _read_json(extract_root / "reports/audit_lite/v4_6_full_local_validation_attestation.json")
        if manifest.get("version") != VERSION:
            errors.append("V4.6 manifest version mismatch in ZIP")
        if scores_report.get("metrics") != manifest.get("metrics"):
            errors.append("V4.6 scores report metrics mismatch in ZIP")
        for flag in [
            "validator_passed",
            "tests_passed",
            "audit_lite_passed",
            "smoke_audit_lite_passed",
            "no_trading",
            "no_backtest",
            "no_orders",
            "no_persistent_model",
        ]:
            if attestation.get(flag) is not True:
                errors.append(f"V4.6 attestation flag must be true: {flag}")
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
    return f"""# Audit ZIP audit-lite V4.6

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
