from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.48_to_V9.51"
ZIP_NAME = "projet-galapagos-v9.48-to-v9.51-audit-lite.zip"
REQUIRED_FILES = [
    "src/galapagos/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.py",
    "src/galapagos/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47.py",
    "src/galapagos/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas.py",
    "src/galapagos/features/aggtrades_exact_5y_feature_enrichment_v9_45.py",
    "src/galapagos/features/aggtrades_exact_5y_feature_enrichment_v9_45_schemas.py",
    "src/galapagos/features/ohlcv_aggtrades_5y_feature_store_v9_37_schemas.py",
    "src/galapagos/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49.py",
    "src/galapagos/datasets/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.py",
    "src/galapagos/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.py",
    "scripts/run_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.py",
    "scripts/run_ohlcv_aggtrades_exact_5y_dataset_v9_49.py",
    "scripts/run_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.py",
    "scripts/run_ohlcv_aggtrades_exact_5y_offline_ml_v9_51.py",
    "scripts/validate_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.py",
    "scripts/validate_ohlcv_aggtrades_exact_5y_dataset_v9_49.py",
    "scripts/validate_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.py",
    "scripts/validate_ohlcv_aggtrades_exact_5y_offline_ml_v9_51.py",
    "scripts/release_audit_lite_zip_v9_48_to_v9_51.py",
    "scripts/audit_audit_lite_zip_v9_48_to_v9_51.py",
    "scripts/smoke_audit_lite_zip_v9_48_to_v9_51.py",
    "reports/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.json",
    "reports/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49.json",
    "reports/datasets/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.json",
    "reports/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.json",
    "reports/research_decisions/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.json",
    "reports/audit_lite/v9_48_to_v9_51_command_results.json",
    "reports/audit_lite/v9_48_to_v9_51_full_local_validation_attestation.json",
    "reports/audit_lite/v9_48_to_v9_51_artifact_inventory.json",
    "reports/audit_lite/zip_size_report_v9_48_to_v9_51.json",
]
FORBIDDEN_PREFIXES = ("data/raw/", "data/silver/", "data/research/", "data/gold/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/", ".git/", ".venv/")
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".zip", ".pem", ".key", ".sha256.json", ".sha256.txt"}


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
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_48_to_v9_51_audit_") as tmp:
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
        errors.extend(_check_inventory(extract_root, names))
        errors.extend(_check_reports(extract_root))
        errors.extend(_check_command_results(extract_root))
    return errors


def _check_inventory(extract_root: Path, names: list[str]) -> list[str]:
    errors: list[str] = []
    inventory = _read_json(extract_root / "reports/audit_lite/v9_48_to_v9_51_artifact_inventory.json")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_48_to_v9_51.json")
    if inventory.get("zip_name") != ZIP_NAME:
        errors.append("inventory zip_name mismatch")
    if inventory.get("files_count") != len(names) or sorted(inventory.get("files", [])) != names:
        errors.append("inventory files do not match ZIP content")
    for payload_name, payload in {"inventory": inventory, "size_report": size_report}.items():
        if not isinstance(payload.get("zip_bytes_estimate"), int) or payload.get("zip_bytes_estimate", 0) <= 0:
            errors.append(f"{payload_name} must contain positive zip_bytes_estimate")
        if payload.get("zip_bytes_is_authoritative") is not False:
            errors.append(f"{payload_name} must mark zip_bytes_is_authoritative=false")
        if payload.get("sidecars_created") is not False or payload.get("zip_fingerprints_created") is not False:
            errors.append(f"{payload_name} must confirm no sidecars and no ZIP fingerprints")
        if _contains_forbidden_zip_field(payload):
            errors.append(f"{payload_name} contains forbidden ZIP fingerprint field")
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    v48 = _read_json(extract_root / "reports/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.json")
    v49 = _read_json(extract_root / "reports/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49.json")
    v50 = _read_json(extract_root / "reports/datasets/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.json")
    v51 = _read_json(extract_root / "reports/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.json")
    group = _read_json(extract_root / "reports/research_decisions/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_48_to_v9_51_full_local_validation_attestation.json")
    if v48.get("decision") not in {"combined_feature_store_validated", "combined_feature_store_validated_with_warnings"}:
        errors.append("V9.48 decision is not successful")
    if v49.get("decision") != "combined_features_5y_dataset_created":
        errors.append("V9.49 decision mismatch")
    if v50.get("decision") != "combined_features_5y_dataset_validated":
        errors.append("V9.50 decision mismatch")
    if v51.get("quality_status") != "PASS" or v51.get("decision") not in {
        "combined_features_5y_ml_completed",
        "combined_features_5y_ml_completed_with_improvement",
        "combined_features_5y_ml_completed_but_weak_vs_baselines",
        "combined_features_5y_ml_completed_but_close_to_shuffled_labels",
        "combined_features_5y_ml_completed_but_class_collapse",
    }:
        errors.append("V9.51 report is not a successful offline ML completion")
    if group.get("v9_51_decision") != v51.get("decision"):
        errors.append("group report/V9.51 decision mismatch")
    for key in ["network_used", "new_data_downloaded", "walk_forward_executed", "backtest_executed", "signal_created", "strategy_created", "model_persisted"]:
        if v51.get(key) is not False or attestation.get(key) is not False:
            errors.append(f"forbidden V9.51/attestation flag must be false: {key}")
    for payload_name, payload in {"v48": v48, "v49": v49, "v50": v50, "v51": v51, "group": group, "attestation": attestation}.items():
        if _contains_forbidden_zip_field(payload):
            errors.append(f"{payload_name} contains forbidden ZIP fingerprint field")
    return errors


def _check_command_results(extract_root: Path) -> list[str]:
    payload = _read_json(extract_root / "reports/audit_lite/v9_48_to_v9_51_command_results.json")
    commands = payload.get("commands", [])
    errors: list[str] = []
    if payload.get("version") != VERSION:
        errors.append("command_results version mismatch")
    for needle in [
        "pytest --collect-only -q",
        "run_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.py",
        "run_ohlcv_aggtrades_exact_5y_dataset_v9_49.py",
        "run_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.py",
        "run_ohlcv_aggtrades_exact_5y_offline_ml_v9_51.py",
        "validate_ohlcv_aggtrades_exact_5y_offline_ml_v9_51.py",
        "release_audit_lite_zip_v9_48_to_v9_51.py",
    ]:
        if not any(needle in item.get("command", "") and item.get("returncode") == 0 for item in commands):
            errors.append(f"missing successful command result for {needle}")
    return errors


def _is_forbidden(name: str) -> bool:
    path = Path(name)
    if any(part in FORBIDDEN_PARTS for part in path.parts):
        return True
    if path.name in FORBIDDEN_NAMES:
        return True
    if any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return True
    return any(path.name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).casefold()
            if "zip_sha256" in lowered or lowered.endswith("_sha256") or lowered == "sha256":
                return True
            if _contains_forbidden_zip_field(value):
                return True
    if isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_reports(result: dict[str, Any]) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_audit_v9_48_to_v9_51.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_48_to_v9_51.md").write_text("# Audit ZIP V9.48 a V9.51\n\n" f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n" f"- Erreurs : `{result['errors']}`.\n" "- Aucun sidecar et aucune empreinte ZIP.\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
