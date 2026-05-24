from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import _bootstrap

_bootstrap.bootstrap_src_path()


VERSION = "V5.6.1"
REPORT_JSON = Path("reports/audit_lite/zip_audit_v5_6_1.json")
REPORT_MD = Path("reports/audit_lite/zip_audit_v5_6_1.md")
REQUIRED_FILES = {
    "README.md",
    "pyproject.toml",
    "reports/manifests/max_history_offline_ml_research_v5_4_manifest.json",
    "reports/ml/max_history_offline_ml_research_v5_4.json",
    "reports/ml/max_history_offline_research_scores_v5_4.json",
    "reports/manifests/max_history_ml_robustness_v5_5_manifest.json",
    "reports/ml/max_history_ml_robustness_v5_5.json",
    "reports/ml/max_history_ml_robustness_v5_5.md",
    "reports/audit_lite/v5_5_full_local_validation_attestation.json",
    "reports/research_decisions/v5_6_research_decision_gate.json",
    "reports/research_decisions/v5_6_research_decision_gate.md",
    "docs/research_decision_gate_v5_6.md",
    "reports/audit_lite/v5_6_1_artifact_inventory.json",
    "reports/audit_lite/v5_6_1_artifact_inventory.md",
    "reports/audit_lite/zip_size_report_v5_6_1.json",
    "reports/audit_lite/zip_size_report_v5_6_1.md",
    "reports/audit_lite/v5_6_1_full_local_validation_attestation.json",
    "reports/audit_lite/v5_6_1_full_local_validation_attestation.md",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_summary.md",
    "scripts/validate_research_decision_gate_v5_6.py",
    "scripts/release_audit_lite_zip_v5_6_1.py",
    "scripts/audit_audit_lite_zip_v5_6_1.py",
    "scripts/smoke_audit_lite_zip_v5_6_1.py",
    "tests/validation/test_research_decision_gate_v5_6.py",
}
REQUIRED_DIR_PREFIXES = [
    "src/galapagos/data/public_market/",
    "src/galapagos/validation/",
]
FORBIDDEN_PREFIXES = [
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
]
FORBIDDEN_SUFFIXES = {".zip", ".parquet", ".pyc", ".pyo", ".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


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
    missing = sorted(REQUIRED_FILES - entry_set)
    if missing:
        errors.append(f"missing required audit-lite files: {missing}")
    for prefix in REQUIRED_DIR_PREFIXES:
        if not any(entry.startswith(prefix) for entry in entries):
            errors.append(f"missing required source package: {prefix}")
    for entry in entries:
        path = Path(entry)
        if "__pycache__" in path.parts:
            errors.append(f"forbidden Python cache found: {entry}")
        if any(entry.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            errors.append(f"forbidden path in audit-lite ZIP: {entry}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden suffix in audit-lite ZIP: {entry}")
        if _is_forbidden_pytest_collectible_script(path):
            errors.append(f"forbidden pytest-collectible script found: {entry}")

    with tempfile.TemporaryDirectory(prefix="galapagos-v5-6-1-audit-") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
        report = _read_json(extract_root / "reports/research_decisions/v5_6_research_decision_gate.json")
        attestation = _read_json(extract_root / "reports/audit_lite/v5_6_1_full_local_validation_attestation.json")
        if report.get("version") != "V5.6" or report.get("correction_version") != VERSION:
            errors.append("V5.6.1 corrected report version mismatch in ZIP")
        if report.get("recommended_next_step") != "B. Ameliorer les features OHLCV avant multi-source.":
            errors.append("V5.6.1 recommended_next_step must be Advanced OHLCV")
        roadmap = report.get("roadmap", [])
        if not roadmap or roadmap[0].get("direction") != "Max Historical Advanced OHLCV Feature Expansion":
            errors.append("V5.6.1 roadmap must start with Advanced OHLCV Feature Expansion")
        for key in ["trading_enabled", "paper_live_enabled", "orders_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled"]:
            if report.get("safety", {}).get(key) is not False:
                errors.append(f"V5.6.1 safety flag must be false: {key}")
        for key in ["strategy_validated", "model_validated_for_trading", "profitability_claimed", "real_trading_allowed"]:
            if report.get("claims", {}).get(key) is not False:
                errors.append(f"V5.6.1 claim flag must be false: {key}")
        for flag in ["validator_passed", "tests_passed", "audit_lite_passed", "smoke_audit_lite_passed", "no_trading", "no_backtest", "no_orders", "no_strategy"]:
            if attestation.get(flag) is not True:
                errors.append(f"V5.6.1 attestation flag must be true: {flag}")
    return _result(zip_path, errors, warnings, entries, top_files)


def _is_forbidden_pytest_collectible_script(path: Path) -> bool:
    return len(path.parts) == 2 and path.parts[0] == "scripts" and path.suffix == ".py" and (
        path.name.startswith("test_") or path.name.endswith("_test.py")
    )


def _result(zip_path: Path, errors: list[str], warnings: list[str], entries: list[str], top_files: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "zip_size_mb": round(zip_path.stat().st_size / 1024 / 1024, 3) if zip_path.exists() else 0.0,
        "entries": len(entries),
        "top_20_largest_files": top_files,
        "raw_zips_absent": not any(entry.endswith(".zip") or entry.startswith("data/raw/") for entry in entries),
        "pytest_collectible_scripts_absent": not any(_is_forbidden_pytest_collectible_script(Path(entry)) for entry in entries),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _render_markdown(result: dict[str, Any]) -> str:
    status = "PASS" if result["passed"] else "FAIL"
    top = "\n".join(f"- `{item['path']}` : {item['bytes']} octets" for item in result["top_20_largest_files"])
    errors = "\n".join(f"- {error}" for error in result["errors"]) or "- Aucune"
    return f"""# Audit ZIP audit-lite V5.6.1

- Statut : `{status}`
- ZIP : `{result['zip_path']}`
- Taille : `{result['zip_size_bytes']}` octets
- Raw zips absents : `{result['raw_zips_absent']}`
- Scripts collectables pytest absents : `{result['pytest_collectible_scripts_absent']}`

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
