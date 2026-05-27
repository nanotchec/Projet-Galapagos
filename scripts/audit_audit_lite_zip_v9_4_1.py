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


VERSION = "V9.4.1"
SOURCE_VERSION = "V9.4"
CORRECTION_SCOPE = "packaging_sidecars_only"
ZIP_NAME = "projet-galapagos-v9.4.1-audit-lite.zip"

REQUIRED_FILES = [
    "scripts/_bootstrap.py",
    "scripts/run_refined_research_decision_gate_v9_4.py",
    "scripts/validate_refined_research_decision_gate_v9_4.py",
    "scripts/release_audit_lite_zip_v9_4_1.py",
    "scripts/audit_audit_lite_zip_v9_4_1.py",
    "scripts/smoke_audit_lite_zip_v9_4_1.py",
    "src/galapagos/research/refined_research_decision_gate_v9_4.py",
    "src/galapagos/research/refined_research_decision_gate_v9_4_validation.py",
    "tests/research/test_refined_research_decision_gate_v9_4.py",
    "tests/validation/test_refined_research_decision_gate_v9_4_validator.py",
    "reports/manifests/refined_research_decision_gate_v9_4_manifest.json",
    "reports/research_decisions/refined_research_decision_gate_v9_4.json",
    "reports/research_decisions/refined_research_decision_gate_v9_4.md",
    "docs/refined_research_decision_gate_v9_4.md",
    "reports/audit_lite/v9_4_1_full_local_validation_attestation.json",
    "reports/audit_lite/v9_4_1_full_local_validation_attestation.md",
    "reports/audit_lite/v9_4_1_artifact_inventory.json",
    "reports/audit_lite/v9_4_1_artifact_inventory.md",
    "reports/audit_lite/zip_size_report_v9_4_1.json",
    "reports/audit_lite/zip_size_report_v9_4_1.md",
    "reports/audit_lite/zip_audit_v9_4_1.json",
    "reports/audit_lite/zip_smoke_v9_4_1.json",
    "reports/audit_lite/v9_4_command_results.json",
    "reports/audit_lite/v9_4_full_local_validation_attestation.json",
    "reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json",
    "reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json",
    "reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.json",
    "reports/ml/refined_strict_walk_forward_validation_v9_3.json",
    "reports/audit_lite/v9_0_to_v9_3_2_full_local_validation_attestation.json",
    "reports/audit_lite/v9_0_to_v9_3_2_artifact_inventory.json",
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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_4_1_audit_") as tmp:
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
    final_bytes = zip_path.stat().st_size
    if payload.get("version") != VERSION:
        errors.append("sidecar JSON version mismatch")
    if payload.get("source_version") != SOURCE_VERSION:
        errors.append("sidecar JSON source_version mismatch")
    if payload.get("correction_scope") != CORRECTION_SCOPE:
        errors.append("sidecar JSON correction_scope mismatch")
    if payload.get("zip_name") != ZIP_NAME:
        errors.append("sidecar JSON zip_name mismatch")
    if payload.get("sha256") != final_sha:
        errors.append("sidecar JSON hash mismatch")
    if payload.get("zip_bytes") != final_bytes:
        errors.append("sidecar JSON ZIP size mismatch")
    expected_txt = f"{final_sha}  {ZIP_NAME}\n"
    if sidecar_txt.read_text(encoding="utf-8") != expected_txt:
        errors.append("sidecar TXT content mismatch")
    return errors


def _check_inventory(extract_root: Path, names: list[str]) -> list[str]:
    errors: list[str] = []
    inventory = _read_json(extract_root / "reports/audit_lite/v9_4_1_artifact_inventory.json")
    if inventory.get("version") != VERSION:
        errors.append("inventory version mismatch")
    if inventory.get("source_version") != SOURCE_VERSION:
        errors.append("inventory source_version mismatch")
    if inventory.get("correction_scope") != CORRECTION_SCOPE:
        errors.append("inventory correction_scope mismatch")
    if inventory.get("zip_name") != ZIP_NAME:
        errors.append("inventory zip_name mismatch")
    if inventory.get("files_count") != len(names):
        errors.append("inventory files_count mismatch")
    if sorted(inventory.get("files", [])) != names:
        errors.append("inventory files list does not match ZIP content")
    if inventory.get("sidecar_is_authoritative") is not True:
        errors.append("inventory must mark sidecar as authoritative")
    for key, value in inventory.get("forbidden_absences_verified", {}).items():
        if value is not True:
            errors.append(f"inventory forbidden absence failed: {key}")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_4_1.json")
    if size_report.get("version") != VERSION:
        errors.append("zip size report version mismatch")
    if size_report.get("source_version") != SOURCE_VERSION:
        errors.append("zip size report source_version mismatch")
    if size_report.get("included_files") != len(names):
        errors.append("zip size report included_files mismatch")
    if size_report.get("sidecar_is_authoritative") is not True:
        errors.append("zip size report must mark sidecar as authoritative")
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    decision = _read_json(extract_root / "reports/research_decisions/refined_research_decision_gate_v9_4.json")
    manifest = _read_json(extract_root / "reports/manifests/refined_research_decision_gate_v9_4_manifest.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_4_1_full_local_validation_attestation.json")
    if decision.get("version") != SOURCE_VERSION or manifest.get("version") != SOURCE_VERSION:
        errors.append("source V9.4 report or manifest version mismatch")
    if decision.get("research_decision") != "backtest_not_justified_refine_labels":
        errors.append("V9.4 research decision must remain unchanged")
    if decision.get("research_decision") == "limited_research_backtest_candidate":
        errors.append("V9.4 must not authorize backtest candidate")
    for key, value in decision.get("findings", {}).items():
        if value is not False:
            errors.append(f"V9.4 finding must be false: {key}")
    for key in ["trading_enabled", "paper_live_enabled", "orders_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled", "api_key_used", "private_endpoint_used"]:
        if decision.get("safety", {}).get(key) is not False:
            errors.append(f"V9.4 safety flag must be false: {key}")
    if decision.get("feature_leakage_scan", {}).get("passed") is not True:
        errors.append("V9.4 feature leakage scan must pass")
    if decision.get("metric_forbidden_scan", {}).get("passed") is not True:
        errors.append("V9.4 metric forbidden scan must pass")
    if attestation.get("version") != VERSION:
        errors.append("V9.4.1 attestation version mismatch")
    if attestation.get("source_version") != SOURCE_VERSION:
        errors.append("V9.4.1 attestation source_version mismatch")
    if attestation.get("correction_scope") != CORRECTION_SCOPE:
        errors.append("V9.4.1 attestation correction_scope mismatch")
    if attestation.get("research_decision") != "backtest_not_justified_refine_labels":
        errors.append("V9.4.1 attestation research decision mismatch")
    if attestation.get("business_results_recalculated") is not False or attestation.get("business_results_modified") is not False:
        errors.append("V9.4.1 must not recalculate or modify business results")
    for key in ["no_trading", "no_paper_live", "no_orders", "no_backtest", "no_strategy", "no_actionable_signal", "no_persistent_model"]:
        if attestation.get(key) is not True:
            errors.append(f"V9.4.1 attestation flag must be true: {key}")
    if attestation.get("api_key_used") is not False or attestation.get("private_endpoint_used") is not False:
        errors.append("V9.4.1 attestation API safety mismatch")
    return errors


def _check_state_surfaces(extract_root: Path) -> list[str]:
    errors: list[str] = []
    project_state = _read_json(extract_root / "reports/PROJECT_STATE.json")
    latest_metrics = _read_json(extract_root / "reports/current/latest_metrics.json")
    latest_summary = (extract_root / "reports/current/latest_summary.md").read_text(encoding="utf-8")
    for label, payload in {"PROJECT_STATE": project_state, "latest_metrics": latest_metrics}.items():
        if payload.get("last_validated_version") != "V9.0_to_V9.3.2":
            errors.append(f"{label} last_validated_version mismatch")
        if payload.get("candidate_version") != VERSION:
            errors.append(f"{label} candidate_version mismatch")
        if payload.get("candidate_status") != "pending_external_audit":
            errors.append(f"{label} candidate_status mismatch")
        if payload.get("source_version") != SOURCE_VERSION:
            errors.append(f"{label} source_version mismatch")
        if payload.get("correction_scope") != CORRECTION_SCOPE:
            errors.append(f"{label} correction_scope mismatch")
        if payload.get("research_decision_v9_4") != "backtest_not_justified_refine_labels":
            errors.append(f"{label} research_decision_v9_4 mismatch")
        for key in ["trading_enabled", "orders_enabled", "backtest_performed", "strategy_enabled", "paper_live_enabled"]:
            if payload.get(key) is not False:
                errors.append(f"{label} safety flag must be false: {key}")
    if VERSION not in latest_summary or SOURCE_VERSION not in latest_summary:
        errors.append("latest_summary must mention V9.4.1 and V9.4")
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
    (report_dir / "zip_audit_v9_4_1.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_4_1.md").write_text(
        "# Audit ZIP V9.4.1\n\n"
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
