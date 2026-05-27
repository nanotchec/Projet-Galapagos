from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.15"
ZIP_NAME = "projet-galapagos-v9.15-audit-lite.zip"

REQUIRED_FILES = [
    "scripts/_bootstrap.py",
    "scripts/run_derivatives_data_extension_readiness_v9_15.py",
    "scripts/validate_derivatives_data_extension_readiness_v9_15.py",
    "scripts/release_audit_lite_zip_v9_15.py",
    "scripts/audit_audit_lite_zip_v9_15.py",
    "scripts/smoke_audit_lite_zip_v9_15.py",
    "src/galapagos/research/derivatives_data_extension_readiness_v9_15.py",
    "src/galapagos/research/derivatives_data_extension_readiness_v9_15_validation.py",
    "tests/research/test_derivatives_data_extension_readiness_v9_15.py",
    "tests/validation/test_derivatives_data_extension_readiness_v9_15_validator.py",
    "reports/manifests/derivatives_data_extension_readiness_v9_15_manifest.json",
    "reports/research_decisions/derivatives_data_extension_readiness_v9_15.json",
    "reports/research_decisions/derivatives_data_extension_readiness_v9_15.md",
    "docs/derivatives_data_extension_readiness_v9_15.md",
    "reports/audit_lite/v9_15_command_results.json",
    "reports/audit_lite/v9_15_full_local_validation_attestation.json",
    "reports/audit_lite/v9_15_artifact_inventory.json",
    "reports/audit_lite/zip_size_report_v9_15.json",
    "reports/audit_lite/zip_audit_v9_15.json",
    "reports/audit_lite/zip_smoke_v9_15.json",
    "reports/research_decisions/feature_label_separability_v9_14_1.json",
    "reports/manifests/feature_label_separability_v9_14_1_manifest.json",
    "reports/research/derivatives_coverage_v1_14.json",
    "reports/research/derivatives_data_quality_v1_14.json",
    "reports/research/derivatives_features_v1_14.json",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_metrics.json",
    "reports/current/latest_summary.md",
    "README.md",
    "pyproject.toml",
]

FORBIDDEN_PREFIXES = ["data/research/", "data/silver/", "data/gold/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/", ".git/", ".venv/"]
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}
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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_15_audit_") as tmp:
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
        errors.extend(_check_inventory(extract_root, names, zip_path))
        errors.extend(_check_reports(extract_root))
        errors.extend(_check_state(extract_root))
    return errors


def _check_inventory(extract_root: Path, names: list[str], zip_path: Path) -> list[str]:
    errors: list[str] = []
    inventory = _read_json(extract_root / "reports/audit_lite/v9_15_artifact_inventory.json")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_15.json")
    if inventory.get("zip_name") != ZIP_NAME:
        errors.append("inventory zip_name mismatch")
    if inventory.get("files_count") != len(names) or sorted(inventory.get("files", [])) != names:
        errors.append("inventory files do not match ZIP content")
    # ZIP byte size is reported for operator convenience only. It is not a
    # blocking invariant because the size report is embedded in the ZIP itself.
    for payload_name, payload in {"inventory": inventory, "size_report": size_report}.items():
        if not isinstance(payload.get("zip_bytes"), int) or payload.get("zip_bytes", 0) <= 0:
            errors.append(f"{payload_name} must contain a positive zip_bytes estimate")
    for payload in [inventory, size_report]:
        if _contains_forbidden_zip_field(payload):
            errors.append("forbidden hash or sidecar field present")
        if payload.get("sidecars_created") is not False or payload.get("zip_fingerprints_created") is not False:
            errors.append("sidecars/fingerprints flags must be false")
    for key, value in inventory.get("forbidden_absences_verified", {}).items():
        if value is not True:
            errors.append(f"forbidden absence failed: {key}")
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    report = _read_json(extract_root / "reports/research_decisions/derivatives_data_extension_readiness_v9_15.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_15_full_local_validation_attestation.json")
    if report.get("v9_15_decision", {}).get("decision") != "derivatives_readiness_not_compatible_with_v9_window":
        errors.append("V9.15 decision mismatch")
    if report.get("features_candidate_created") is not False:
        errors.append("V9.15 must not create features in this ZIP")
    if report.get("funding_readiness", {}).get("compatible_with_v9_window") is not False:
        errors.append("funding must be incompatible with V9 window")
    if report.get("open_interest_readiness", {}).get("compatible_with_v9_window") is not False:
        errors.append("open interest must be incompatible with V9 window")
    if report.get("v9_chain_compatibility", {}).get("compatible_with_current_v9_chain") is not False:
        errors.append("current V9 chain compatibility must be false")
    for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced", "walk_forward_validated_for_trading"]:
        if report.get("findings", {}).get(key) is not False:
            errors.append(f"finding must be false: {key}")
    for key in ["no_trading", "no_paper_live", "no_orders", "no_backtest", "no_walk_forward", "no_strategy", "no_actionable_signal", "no_persistent_model", "no_sidecars", "no_zip_fingerprints", "no_new_data_download"]:
        if attestation.get(key) is not True:
            errors.append(f"attestation must confirm {key}=true")
    for key in ["api_key_used", "private_endpoint_used", "network_used"]:
        if attestation.get(key) is not False:
            errors.append(f"attestation must confirm {key}=false")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.15 report contains forbidden ZIP hash or sidecar field")
    return errors


def _check_state(extract_root: Path) -> list[str]:
    errors: list[str] = []
    state = _read_json(extract_root / "reports/PROJECT_STATE.json")
    metrics = _read_json(extract_root / "reports/current/latest_metrics.json")
    for name, payload in {"PROJECT_STATE": state, "latest_metrics": metrics}.items():
        if payload.get("last_validated_version") != "V9.14.1":
            errors.append(f"{name} last_validated_version mismatch")
        if payload.get("candidate_version") != VERSION:
            errors.append(f"{name} candidate_version mismatch")
        if payload.get("candidate_status") != "pending_external_audit":
            errors.append(f"{name} candidate_status mismatch")
        if payload.get("network_used") is not False or payload.get("no_new_data_download") is not True:
            errors.append(f"{name} must confirm no network and no download")
        if payload.get("no_sidecars") is not True or payload.get("no_zip_fingerprints") is not True:
            errors.append(f"{name} must confirm no sidecars and no ZIP fingerprints")
        if payload.get("no_walk_forward") is not True:
            errors.append(f"{name} must confirm no walk-forward")
        if "recommended_next_version" in payload or "recommended_next_action" in payload:
            errors.append(f"{name} contains stale unversioned recommendation fields")
    return errors


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            text = str(key).casefold()
            if text == "zip_sha256" or text.startswith("sidecar_"):
                return True
            if _contains_forbidden_zip_field(value):
                return True
    elif isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _is_forbidden(name: str) -> bool:
    path = Path(name)
    if name.endswith(".sha256.json") or name.endswith(".sha256.txt"):
        return True
    if any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return True
    if path.name in FORBIDDEN_NAMES:
        return True
    if set(path.parts) & FORBIDDEN_PARTS:
        return True
    return path.suffix.casefold() in FORBIDDEN_SUFFIXES


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_reports(result: dict[str, Any]) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_audit_v9_15.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_15.md").write_text(f"# Audit ZIP V9.15\n\n- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n- Erreurs : `{result['errors']}`.\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
