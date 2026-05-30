from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.34.1"
ZIP_NAME = "projet-galapagos-v9.34.1-audit-lite.zip"

REQUIRED_FILES = [
    "scripts/_bootstrap.py",
    "src/galapagos/data/public_market/config.py",
    "src/galapagos/data/public_market/storage.py",
    "src/galapagos/data/public_market/sources/binance_archive.py",
    "src/galapagos/data/ohlcv_5y_extension_v9_34.py",
    "src/galapagos/data/ohlcv_5y_extension_v9_34_validation.py",
    "src/galapagos/data/ohlcv_5y_extension_correction_v9_34_1.py",
    "src/galapagos/data/ohlcv_5y_extension_correction_v9_34_1_validation.py",
    "scripts/run_ohlcv_5y_extension_correction_v9_34_1.py",
    "scripts/validate_ohlcv_5y_extension_correction_v9_34_1.py",
    "scripts/release_audit_lite_zip_v9_34_1.py",
    "scripts/audit_audit_lite_zip_v9_34_1.py",
    "scripts/smoke_audit_lite_zip_v9_34_1.py",
    "tests/data/test_ohlcv_5y_extension_correction_v9_34_1.py",
    "tests/validation/test_ohlcv_5y_extension_correction_v9_34_1_validator.py",
    "reports/manifests/ohlcv_5y_extension_correction_v9_34_1_manifest.json",
    "reports/data/ohlcv_5y_extension_correction_v9_34_1.json",
    "reports/data/ohlcv_5y_extension_correction_v9_34_1.md",
    "docs/ohlcv_5y_extension_correction_v9_34_1.md",
    "reports/audit_lite/v9_34_1_command_results.json",
    "reports/audit_lite/v9_34_1_command_results.md",
    "reports/audit_lite/v9_34_1_full_local_validation_attestation.json",
    "reports/audit_lite/v9_34_1_full_local_validation_attestation.md",
    "reports/audit_lite/v9_34_1_artifact_inventory.json",
    "reports/audit_lite/v9_34_1_artifact_inventory.md",
    "reports/audit_lite/zip_size_report_v9_34_1.json",
    "reports/audit_lite/zip_size_report_v9_34_1.md",
    "reports/audit_lite/zip_audit_v9_34_1.json",
    "reports/audit_lite/zip_audit_v9_34_1.md",
    "reports/audit_lite/zip_smoke_v9_34_1.json",
    "reports/audit_lite/zip_smoke_v9_34_1.md",
    "reports/data/ohlcv_5y_extension_v9_34.json",
    "reports/data/ohlcv_5y_extension_v9_34.md",
    "reports/manifests/ohlcv_5y_extension_v9_34_manifest.json",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_metrics.json",
    "reports/current/latest_summary.md",
    "README.md",
    "pyproject.toml",
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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_34_1_audit_") as tmp:
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
        errors.extend(_check_state(extract_root))
    return errors


def _check_inventory(extract_root: Path, names: list[str]) -> list[str]:
    errors: list[str] = []
    inventory = _read_json(extract_root / "reports/audit_lite/v9_34_1_artifact_inventory.json")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_34_1.json")
    if inventory.get("zip_name") != ZIP_NAME:
        errors.append("inventory zip_name mismatch")
    if inventory.get("files_count") != len(names) or sorted(inventory.get("files", [])) != names:
        errors.append("inventory files do not match ZIP content")
    for payload_name, payload in {"inventory": inventory, "size_report": size_report}.items():
        if not isinstance(payload.get("zip_bytes_estimate"), int) or payload.get("zip_bytes_estimate", 0) <= 0:
            errors.append(f"{payload_name} must contain a positive zip_bytes_estimate")
        if payload.get("zip_bytes_is_authoritative") is not False:
            errors.append(f"{payload_name} must mark zip_bytes_is_authoritative=false")
        if payload.get("sidecars_created") is not False or payload.get("zip_fingerprints_created") is not False:
            errors.append(f"{payload_name} must confirm no sidecars and no ZIP fingerprints")
        if _contains_forbidden_zip_field(payload):
            errors.append(f"{payload_name} contains forbidden ZIP fingerprint or sidecar field")
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    report = _read_json(extract_root / "reports/data/ohlcv_5y_extension_correction_v9_34_1.json")
    manifest = _read_json(extract_root / "reports/manifests/ohlcv_5y_extension_correction_v9_34_1_manifest.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_34_1_full_local_validation_attestation.json")
    if report.get("version") != VERSION or report.get("source_version") != "V9.34":
        errors.append("V9.34.1 report version/source mismatch")
    if manifest.get("decision") != report.get("decision") or manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.34.1 manifest mismatch")
    if report.get("feature_store_created") is not False or report.get("combined_feature_store_created") is not False:
        errors.append("V9.34.1 must not create a feature store")
    if report.get("labels_created") is not False or report.get("dataset_created") is not False or report.get("ml_executed") is not False:
        errors.append("V9.34.1 must not create labels, dataset or ML")
    if report.get("walk_forward_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.34.1 must not run walk-forward or backtest")
    if "before" not in report.get("bad_day_diagnostic", {}) or "repair" not in report.get("bad_day_diagnostic", {}):
        errors.append("V9.34.1 report must contain bad-day diagnostic")
    errors.extend(_check_flags(report, attestation))
    for payload_name, payload in {"report": report, "manifest": manifest, "attestation": attestation}.items():
        if _contains_forbidden_zip_field(payload):
            errors.append(f"{payload_name} contains forbidden ZIP fingerprint or sidecar field")
    return errors


def _check_flags(report: dict[str, Any], attestation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["no_trading", "no_paper_live", "no_orders", "no_backtest", "no_walk_forward", "no_ml", "no_dataset_supervised", "no_labels", "no_strategy", "no_actionable_signal", "no_persistent_model", "no_destructive_cleanup", "no_sidecars", "no_zip_fingerprints", "no_combined_feature_store"]:
        if report.get("safety_flags", {}).get(key) is not True or attestation.get(key) is not True:
            errors.append(f"must confirm {key}=true")
    for key in ["api_key_used", "private_endpoint_used", "exchange_auth_used", "websocket_live_used"]:
        if report.get("safety_flags", {}).get(key) is not False or attestation.get(key) is not False:
            errors.append(f"must confirm {key}=false")
    return errors


def _check_command_results(extract_root: Path) -> list[str]:
    payload = _read_json(extract_root / "reports/audit_lite/v9_34_1_command_results.json")
    commands = payload.get("commands", [])
    errors: list[str] = []
    if payload.get("version") != VERSION:
        errors.append("command_results version mismatch")
    if not commands:
        return ["command_results must contain executed commands"]
    report = _read_json(extract_root / "reports/data/ohlcv_5y_extension_correction_v9_34_1.json")
    for needle in [
        "pytest --collect-only -q",
        "test_ohlcv_5y_extension_correction_v9_34_1.py",
        "test_ohlcv_5y_extension_correction_v9_34_1_validator.py",
        "validate_ohlcv_5y_extension_correction_v9_34_1.py",
        "release_audit_lite_zip_v9_34_1.py",
    ]:
        if not any(needle in item.get("command", "") and item.get("returncode") == 0 for item in commands):
            errors.append(f"missing successful command result for {needle}")
    run_results = [item for item in commands if "run_ohlcv_5y_extension_correction_v9_34_1.py" in item.get("command", "")]
    if not run_results:
        errors.append("missing command result for run_ohlcv_5y_extension_correction_v9_34_1.py")
    elif report.get("decision") in {"ohlcv_5y_extension_failed_quality", "ohlcv_5y_extension_failed_source_issue", "ohlcv_5y_extension_failed_storage"}:
        if not any(item.get("returncode") in {0, 1} for item in run_results):
            errors.append("failed V9.34.1 run command must be captured with returncode 0 or 1")
    elif not any(item.get("returncode") == 0 for item in run_results):
        errors.append("missing successful command result for run_ohlcv_5y_extension_correction_v9_34_1.py")
    if payload.get("sidecars_created") is not False or payload.get("zip_fingerprints_created") is not False:
        errors.append("command_results must confirm no sidecars and no ZIP fingerprints")
    return errors


def _check_state(extract_root: Path) -> list[str]:
    metrics = _read_json(extract_root / "reports/current/latest_metrics.json")
    errors: list[str] = []
    if metrics.get("last_validated_version") != "V9.33":
        errors.append("latest_metrics last_validated_version mismatch")
    if metrics.get("candidate_version") != VERSION or metrics.get("candidate_status") != "pending_external_audit":
        errors.append("latest_metrics candidate mismatch")
    if metrics.get("direction") != "ohlcv_5y_extension_correction":
        errors.append("latest_metrics direction mismatch")
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
    elif isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_reports(result: dict[str, Any]) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_audit_v9_34_1.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_34_1.md").write_text("# Audit ZIP V9.34.1\n\n" f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n" f"- Erreurs : `{result['errors']}`.\n" "- Aucun sidecar et aucune empreinte ZIP.\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
