from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.5"
ZIP_NAME = "projet-galapagos-v9.5-audit-lite.zip"

REQUIRED_FILES = [
    "scripts/_bootstrap.py",
    "scripts/run_alternative_label_design_audit_v9_5.py",
    "scripts/validate_alternative_label_design_audit_v9_5.py",
    "scripts/release_audit_lite_zip_v9_5.py",
    "scripts/audit_audit_lite_zip_v9_5.py",
    "scripts/smoke_audit_lite_zip_v9_5.py",
    "src/galapagos/research/alternative_label_design_audit_v9_5.py",
    "src/galapagos/research/alternative_label_design_audit_v9_5_validation.py",
    "tests/research/test_alternative_label_design_audit_v9_5.py",
    "tests/validation/test_alternative_label_design_audit_v9_5_validator.py",
    "reports/manifests/alternative_label_design_audit_v9_5_manifest.json",
    "reports/research_decisions/alternative_label_design_audit_v9_5.json",
    "reports/research_decisions/alternative_label_design_audit_v9_5.md",
    "docs/alternative_label_design_audit_v9_5.md",
    "reports/audit_lite/v9_5_command_results.json",
    "reports/audit_lite/v9_5_command_results.md",
    "reports/audit_lite/v9_5_full_local_validation_attestation.json",
    "reports/audit_lite/v9_5_full_local_validation_attestation.md",
    "reports/audit_lite/v9_5_artifact_inventory.json",
    "reports/audit_lite/v9_5_artifact_inventory.md",
    "reports/audit_lite/zip_size_report_v9_5.json",
    "reports/audit_lite/zip_size_report_v9_5.md",
    "reports/audit_lite/zip_audit_v9_5.json",
    "reports/audit_lite/zip_smoke_v9_5.json",
    "reports/research_decisions/refined_research_decision_gate_v9_4.json",
    "reports/manifests/refined_research_decision_gate_v9_4_manifest.json",
    "reports/audit_lite/v9_4_1_full_local_validation_attestation.json",
    "reports/audit_lite/v9_4_1_artifact_inventory.json",
    "reports/ml/refined_strict_walk_forward_validation_v9_3.json",
    "reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.json",
    "reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json",
    "reports/manifests/max_history_label_factory_v5_2_manifest.json",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_metrics.json",
    "reports/current/latest_summary.md",
    "README.md",
    "pyproject.toml",
]

FORBIDDEN_PREFIXES = [
    "data/research/",
    "reports/backtests/",
    "reports/strategies/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
    ".git/",
    ".venv/",
]
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_NAMES = {".DS_Store", ".env"}
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".zip", ".pem", ".key"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    zip_path = Path(args.zip_path).resolve()
    result = {"version": VERSION, "zip": str(zip_path), "passed": False, "errors": audit_zip(zip_path)}
    result["passed"] = not result["errors"]
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


def audit_zip(zip_path: Path) -> list[str]:
    if not zip_path.exists():
        return [f"missing zip: {zip_path}"]
    if not zipfile.is_zipfile(zip_path):
        return [f"not a valid zip: {zip_path}"]
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_5_audit_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = sorted(archive.namelist())
            archive.extractall(extract_root)
        missing = [path for path in REQUIRED_FILES if path not in names]
        if missing:
            errors.append(f"missing required files: {missing}")
        forbidden = [name for name in names if _is_forbidden(name)]
        if forbidden:
            errors.append(f"forbidden files present: {forbidden[:50]}")
        errors.extend(_check_sidecars(zip_path))
        errors.extend(_check_inventory(extract_root, names))
        errors.extend(_check_reports(extract_root))
        errors.extend(_check_state_surfaces(extract_root))
    return errors


def _check_sidecars(zip_path: Path) -> list[str]:
    errors: list[str] = []
    sidecar_json = zip_path.with_name(zip_path.name + ".sha256.json")
    sidecar_txt = zip_path.with_name(zip_path.name + ".sha256.txt")
    if not sidecar_json.exists():
        errors.append(f"missing sidecar JSON: {sidecar_json}")
        return errors
    if not sidecar_txt.exists():
        errors.append(f"missing sidecar TXT: {sidecar_txt}")
        return errors
    payload = _read_json(sidecar_json)
    final_sha = _sha256_file(zip_path)
    if payload.get("version") != VERSION:
        errors.append("sidecar JSON version mismatch")
    if payload.get("zip_name") != ZIP_NAME:
        errors.append("sidecar JSON zip_name mismatch")
    if payload.get("sha256") != final_sha:
        errors.append("sidecar JSON hash mismatch")
    if payload.get("zip_bytes") != zip_path.stat().st_size:
        errors.append("sidecar JSON ZIP size mismatch")
    if sidecar_txt.read_text(encoding="utf-8") != f"{final_sha}  {ZIP_NAME}\n":
        errors.append("sidecar TXT content mismatch")
    return errors


def _check_inventory(extract_root: Path, names: list[str]) -> list[str]:
    errors: list[str] = []
    inventory = _read_json(extract_root / "reports/audit_lite/v9_5_artifact_inventory.json")
    if inventory.get("version") != VERSION:
        errors.append("inventory version mismatch")
    if inventory.get("zip_name") != ZIP_NAME:
        errors.append("inventory zip_name mismatch")
    if inventory.get("files_count") != len(names):
        errors.append("inventory files_count mismatch")
    if sorted(inventory.get("files", [])) != names:
        errors.append("inventory files list does not match ZIP content")
    for key, value in inventory.get("forbidden_absences_verified", {}).items():
        if value is not True:
            errors.append(f"inventory forbidden absence failed: {key}")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_5.json")
    if size_report.get("included_files") != len(names):
        errors.append("zip size report included_files mismatch")
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    report = _read_json(extract_root / "reports/research_decisions/alternative_label_design_audit_v9_5.json")
    manifest = _read_json(extract_root / "reports/manifests/alternative_label_design_audit_v9_5_manifest.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_5_full_local_validation_attestation.json")
    if report.get("version") != VERSION or manifest.get("version") != VERSION:
        errors.append("V9.5 report or manifest version mismatch")
    if report.get("source_decision", {}).get("research_decision") != "backtest_not_justified_refine_labels":
        errors.append("V9.5 source decision mismatch")
    if report.get("v9_5_decision", {}).get("decision") == "limited_research_backtest_candidate":
        errors.append("V9.5 must not recommend a backtest candidate")
    if report.get("v9_5_decision", {}).get("next_step") != "V9.6 - Refined Label Factory Candidate":
        errors.append("V9.5 next step mismatch")
    for key, value in report.get("findings", {}).items():
        if value is not False:
            errors.append(f"V9.5 finding must be false: {key}")
    for key in ["trading_enabled", "paper_live_enabled", "orders_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled", "api_key_used", "private_endpoint_used"]:
        if report.get("safety", {}).get(key) is not False:
            errors.append(f"V9.5 safety flag must be false: {key}")
    if report.get("leakage_guard", {}).get("passed") is not True:
        errors.append("V9.5 leakage guard must pass")
    if report.get("forbidden_output_scan", {}).get("passed") is not True:
        errors.append("V9.5 forbidden output scan must pass")
    if attestation.get("version") != VERSION:
        errors.append("V9.5 attestation version mismatch")
    for key in ["no_trading", "no_paper_live", "no_orders", "no_backtest", "no_strategy", "no_actionable_signal", "no_persistent_model"]:
        if attestation.get(key) is not True:
            errors.append(f"V9.5 attestation flag must be true: {key}")
    if attestation.get("api_key_used") is not False or attestation.get("private_endpoint_used") is not False:
        errors.append("V9.5 attestation API safety mismatch")
    return errors


def _check_state_surfaces(extract_root: Path) -> list[str]:
    errors: list[str] = []
    project_state = _read_json(extract_root / "reports/PROJECT_STATE.json")
    latest_metrics = _read_json(extract_root / "reports/current/latest_metrics.json")
    latest_summary = (extract_root / "reports/current/latest_summary.md").read_text(encoding="utf-8")
    for label, payload in {"PROJECT_STATE": project_state, "latest_metrics": latest_metrics}.items():
        if payload.get("last_validated_version") != "V9.4.1":
            errors.append(f"{label} last_validated_version mismatch")
        if payload.get("candidate_version") != VERSION:
            errors.append(f"{label} candidate_version mismatch")
        if payload.get("candidate_status") != "pending_external_audit":
            errors.append(f"{label} candidate_status mismatch")
        if payload.get("direction") != "alternative_label_design_audit":
            errors.append(f"{label} direction mismatch")
        for key in ["trading_enabled", "orders_enabled", "backtest_performed", "strategy_enabled", "paper_live_enabled"]:
            if payload.get(key) is not False:
                errors.append(f"{label} safety flag must be false: {key}")
    if VERSION not in latest_summary:
        errors.append("latest_summary must mention V9.5")
    return errors


def _is_forbidden(name: str) -> bool:
    path = Path(name)
    if any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return True
    if set(path.parts) & FORBIDDEN_PARTS:
        return True
    if path.name in FORBIDDEN_NAMES:
        return True
    return path.suffix.casefold() in FORBIDDEN_SUFFIXES


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_reports(result: dict[str, Any]) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_audit_v9_5.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_5.md").write_text(
        "# Audit ZIP V9.5\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n",
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
