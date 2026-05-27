from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.14"
ZIP_NAME = "projet-galapagos-v9.14-audit-lite.zip"

REQUIRED_FILES = [
    "scripts/_bootstrap.py",
    "scripts/run_feature_label_separability_v9_14.py",
    "scripts/validate_feature_label_separability_v9_14.py",
    "scripts/release_audit_lite_zip_v9_14.py",
    "scripts/audit_audit_lite_zip_v9_14.py",
    "scripts/smoke_audit_lite_zip_v9_14.py",
    "src/galapagos/research/feature_label_separability_v9_14.py",
    "src/galapagos/research/feature_label_separability_v9_14_validation.py",
    "tests/research/test_feature_label_separability_v9_14.py",
    "tests/validation/test_feature_label_separability_v9_14_validator.py",
    "reports/manifests/feature_label_separability_v9_14_manifest.json",
    "reports/research_decisions/feature_label_separability_v9_14.json",
    "reports/research_decisions/feature_label_separability_v9_14.md",
    "docs/feature_label_separability_v9_14.md",
    "reports/audit_lite/v9_14_command_results.json",
    "reports/audit_lite/v9_14_full_local_validation_attestation.json",
    "reports/audit_lite/v9_14_artifact_inventory.json",
    "reports/audit_lite/zip_size_report_v9_14.json",
    "reports/audit_lite/zip_audit_v9_14.json",
    "reports/audit_lite/zip_smoke_v9_14.json",
    "reports/datasets/h4_label_candidate_dataset_v9_13.json",
    "reports/ml/h4_label_candidate_offline_ml_v9_13.json",
    "reports/ml/h4_label_candidate_offline_scores_v9_13.json",
    "reports/labels/horizon_event_label_redesign_v9_12.json",
    "reports/research_decisions/label_failure_analysis_v9_11.json",
    "reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.json",
    "reports/ml/refined_volnorm_labels_offline_ml_v9_8.json",
    "reports/ml/refined_volnorm_strict_walk_forward_v9_9.json",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_metrics.json",
    "reports/current/latest_summary.md",
    "README.md",
    "pyproject.toml",
]

REQUIRED_SAMPLES = [
    "data/audit_lite/v9_13/datasets/timeframe=1m/dataset_sample.parquet",
    "data/audit_lite/v9_13/datasets/timeframe=5m/dataset_sample.parquet",
    "data/audit_lite/v9_13/datasets/timeframe=15m/dataset_sample.parquet",
    "data/audit_lite/v9_13/datasets/timeframe=1h/dataset_sample.parquet",
    "data/audit_lite/v9_13/ml_scores/timeframe=1m/ml-scores_sample.parquet",
    "data/audit_lite/v9_13/ml_scores/timeframe=5m/ml-scores_sample.parquet",
    "data/audit_lite/v9_13/ml_scores/timeframe=15m/ml-scores_sample.parquet",
    "data/audit_lite/v9_13/ml_scores/timeframe=1h/ml-scores_sample.parquet",
]

FORBIDDEN_PREFIXES = ["data/research/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/", ".git/", ".venv/"]
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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_14_audit_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = sorted(archive.namelist())
            archive.extractall(extract_root)
        missing = [path for path in [*REQUIRED_FILES, *REQUIRED_SAMPLES] if path not in names]
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
    inventory = _read_json(extract_root / "reports/audit_lite/v9_14_artifact_inventory.json")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_14.json")
    if inventory.get("zip_name") != ZIP_NAME:
        errors.append("inventory zip_name mismatch")
    if inventory.get("files_count") != len(names) or sorted(inventory.get("files", [])) != names:
        errors.append("inventory files do not match ZIP content")
    if inventory.get("zip_bytes") != zip_path.stat().st_size or size_report.get("zip_bytes") != zip_path.stat().st_size:
        errors.append("ZIP byte report mismatch")
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
    report = _read_json(extract_root / "reports/research_decisions/feature_label_separability_v9_14.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_14_full_local_validation_attestation.json")
    if report.get("v9_14_decision", {}).get("decision") not in {"feature_first_before_more_labels", "label_redesign_binary_directional_candidate", "label_redesign_quantile_candidate", "extend_data_first_before_more_labels", "stop_refined_label_branch", "inconclusive_need_manual_review"}:
        errors.append("V9.14 decision mismatch")
    if report.get("safety_flags", {}).get("no_walk_forward") is not True:
        errors.append("V9.14 must confirm no walk-forward")
    if report.get("ml_diagnostic_v9_13", {}).get("walk_forward_not_repeated_in_v9_14") is not True:
        errors.append("V9.14 report repeated walk-forward")
    for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced", "walk_forward_validated_for_trading"]:
        if report.get("findings", {}).get(key) is not False:
            errors.append(f"finding must be false: {key}")
    for key in ["no_trading", "no_paper_live", "no_orders", "no_backtest", "no_walk_forward", "no_strategy", "no_actionable_signal", "no_persistent_model", "no_sidecars", "no_zip_fingerprints"]:
        if attestation.get(key) is not True:
            errors.append(f"attestation must confirm {key}=true")
    for key in ["api_key_used", "private_endpoint_used"]:
        if attestation.get(key) is not False:
            errors.append(f"attestation must confirm {key}=false")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.14 report contains forbidden ZIP hash or sidecar field")
    return errors


def _check_state(extract_root: Path) -> list[str]:
    errors: list[str] = []
    state = _read_json(extract_root / "reports/PROJECT_STATE.json")
    metrics = _read_json(extract_root / "reports/current/latest_metrics.json")
    for name, payload in {"PROJECT_STATE": state, "latest_metrics": metrics}.items():
        if payload.get("last_validated_version") != "V9.13":
            errors.append(f"{name} last_validated_version mismatch")
        if payload.get("candidate_version") != VERSION:
            errors.append(f"{name} candidate_version mismatch")
        if payload.get("candidate_status") != "pending_external_audit":
            errors.append(f"{name} candidate_status mismatch")
        if payload.get("no_sidecars") is not True or payload.get("no_zip_fingerprints") is not True:
            errors.append(f"{name} must confirm no sidecars and no ZIP fingerprints")
        if payload.get("no_walk_forward") is not True:
            errors.append(f"{name} must confirm no walk-forward")
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
    (report_dir / "zip_audit_v9_14.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_14.md").write_text(f"# Audit ZIP V9.14\n\n- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n- Erreurs : `{result['errors']}`.\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
