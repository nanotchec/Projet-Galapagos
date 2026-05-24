from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any


VERSION = "V6.2"
AUDIT_JSON = Path("reports/audit_lite/zip_audit_v6_2.json")
AUDIT_MD = Path("reports/audit_lite/zip_audit_v6_2.md")
REQUIRED_SOURCE_PREFIXES = [
    "src/galapagos/data/public_market/",
    "src/galapagos/features/",
    "src/galapagos/labels/",
    "src/galapagos/datasets/",
    "src/galapagos/ml/",
    "src/galapagos/validation/",
]
REQUIRED_ENTRIES = {
    "reports/manifests/advanced_ohlcv_offline_ml_research_v6_2_manifest.json",
    "reports/ml/advanced_ohlcv_offline_ml_research_v6_2.json",
    "reports/ml/advanced_ohlcv_offline_ml_research_v6_2.md",
    "reports/ml/advanced_ohlcv_offline_research_scores_v6_2.json",
    "reports/ml/advanced_ohlcv_offline_research_scores_v6_2.md",
    "reports/audit_lite/v6_2_full_local_validation_attestation.json",
    "reports/audit_lite/v6_2_full_local_validation_attestation.md",
    "reports/audit_lite/v6_2_artifact_inventory.json",
    "reports/audit_lite/v6_2_parquet_summary.json",
    "docs/advanced_ohlcv_offline_ml_research_v6_2.md",
    "scripts/run_advanced_ohlcv_offline_ml_research_v6_2.py",
    "scripts/validate_advanced_ohlcv_offline_ml_research_v6_2.py",
    "scripts/release_audit_lite_zip_v6_2.py",
    "scripts/audit_audit_lite_zip_v6_2.py",
    "scripts/smoke_audit_lite_zip_v6_2.py",
    "tests/ml/test_advanced_ohlcv_offline_ml_research_v6_2.py",
    "tests/validation/test_advanced_ohlcv_offline_ml_research_v6_2_validator.py",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_summary.md",
    "README.md",
    "pyproject.toml",
}
SAMPLE_ENTRIES = {
    "data/audit_lite/v6_2/ml_scores/timeframe=1m/sample.parquet",
    "data/audit_lite/v6_2/ml_scores/timeframe=5m/sample.parquet",
    "data/audit_lite/v6_2/ml_scores/timeframe=15m/sample.parquet",
    "data/audit_lite/v6_2/ml_scores/timeframe=1h/sample.parquet",
}
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
FORBIDDEN_SUFFIXES = (".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pyc")
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

    for prefix in REQUIRED_SOURCE_PREFIXES:
        if not any(entry.startswith(prefix) for entry in entries):
            errors.append(f"missing required source package: {prefix}")
    missing = sorted((REQUIRED_ENTRIES | SAMPLE_ENTRIES) - entry_set)
    errors.extend(f"missing required entry: {entry}" for entry in missing)

    for entry in entries:
        if _is_forbidden_pytest_collectible_script(entry):
            errors.append(f"forbidden pytest-collectible script found: {entry}")
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


def _is_forbidden_pytest_collectible_script(entry: str) -> bool:
    path = Path(entry)
    if len(path.parts) != 2 or path.parts[0] != "scripts" or path.suffix != ".py":
        return False
    name = path.name
    return name in {"run_forward_paper_test.py", "test_llm_provider.py"} or name.startswith("test_") or name.endswith("_test.py")


def _is_forbidden_artifact(entry: str) -> bool:
    path = Path(entry)
    if any(part in FORBIDDEN_PARTS for part in path.parts):
        return True
    if entry.startswith(FORBIDDEN_PREFIXES):
        return True
    if entry.endswith(FORBIDDEN_SUFFIXES):
        return True
    if entry.endswith(".parquet") and entry not in SAMPLE_ENTRIES:
        return True
    if entry.endswith(".zip"):
        return True
    return False


def _result(zip_path: Path, size: int, entries: list[str], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    largest = []
    if zip_path.exists():
        with zipfile.ZipFile(zip_path) as archive:
            largest = sorted(
                [{"path": item.filename, "bytes": item.file_size} for item in archive.infolist()],
                key=lambda item: item["bytes"],
                reverse=True,
            )[:20]
    return {
        "version": VERSION,
        "zip_path": str(zip_path),
        "zip_size_bytes": int(size),
        "zip_size_mb": round(size / 1024 / 1024, 3) if size else 0,
        "entries": len(entries),
        "top_20_largest_files": largest,
        "pytest_collectible_scripts_absent": not any(_is_forbidden_pytest_collectible_script(entry) for entry in entries),
        "raw_zips_absent": not any(entry.startswith("data/raw/") for entry in entries),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _write_reports(result: dict[str, Any]) -> None:
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Audit ZIP V6.2",
        "",
        f"- ZIP : `{result['zip_path']}`.",
        f"- Taille : `{result['zip_size_bytes']}` octets.",
        f"- Entrees : `{result['entries']}`.",
        f"- Scripts pytest collectables absents : `{result['pytest_collectible_scripts_absent']}`.",
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.",
        f"- Erreurs : `{len(result['errors'])}`.",
    ]
    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
