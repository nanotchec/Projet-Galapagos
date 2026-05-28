from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.25.1"
ZIP_NAME = "projet-galapagos-v9.25.1-audit-lite.zip"

REQUIRED_FILES = [
    "scripts/_bootstrap.py",
    "scripts/run_aggtrades_post_v9_resume_campaign_v9_25_1.py",
    "scripts/validate_aggtrades_post_v9_resume_campaign_v9_25_1.py",
    "scripts/release_audit_lite_zip_v9_25_1.py",
    "scripts/audit_audit_lite_zip_v9_25_1.py",
    "scripts/smoke_audit_lite_zip_v9_25_1.py",
    "src/galapagos/data/aggtrades_post_v9_collection_v9_18.py",
    "src/galapagos/data/aggtrades_post_v9_batch3_collection_v9_24.py",
    "src/galapagos/data/aggtrades_post_v9_completion_campaign_v9_25.py",
    "src/galapagos/data/aggtrades_post_v9_resume_campaign_v9_25_1.py",
    "src/galapagos/data/aggtrades_post_v9_resume_campaign_v9_25_1_validation.py",
    "tests/data/test_aggtrades_post_v9_resume_campaign_v9_25_1.py",
    "tests/validation/test_aggtrades_post_v9_resume_campaign_v9_25_1_validator.py",
    "reports/manifests/aggtrades_post_v9_resume_campaign_v9_25_1_manifest.json",
    "reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.json",
    "reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.md",
    "docs/aggtrades_post_v9_resume_campaign_v9_25_1.md",
    "reports/audit_lite/v9_25_1_command_results.json",
    "reports/audit_lite/v9_25_1_command_results.md",
    "reports/audit_lite/v9_25_1_full_local_validation_attestation.json",
    "reports/audit_lite/v9_25_1_full_local_validation_attestation.md",
    "reports/audit_lite/v9_25_1_artifact_inventory.json",
    "reports/audit_lite/v9_25_1_artifact_inventory.md",
    "reports/audit_lite/zip_size_report_v9_25_1.json",
    "reports/audit_lite/zip_size_report_v9_25_1.md",
    "reports/audit_lite/zip_audit_v9_25_1.json",
    "reports/audit_lite/zip_audit_v9_25_1.md",
    "reports/audit_lite/zip_smoke_v9_25_1.json",
    "reports/audit_lite/zip_smoke_v9_25_1.md",
    "reports/data/aggtrades_post_v9_completion_campaign_v9_25.json",
    "reports/data/aggtrades_post_v9_completion_batch01_v9_25.json",
    "reports/data/aggtrades_post_v9_batch3_collection_v9_24.json",
    "reports/data/aggtrades_post_v9_batch2_collection_v9_23.json",
    "reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.json",
    "reports/data/aggtrades_post_v9_batch_expansion_v9_21.json",
    "reports/data/aggtrades_post_v9_batch_collection_v9_20.json",
    "reports/data/aggtrades_post_v9_pilot_collection_v9_19.json",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_metrics.json",
    "reports/current/latest_summary.md",
    "README.md",
    "pyproject.toml",
]

FORBIDDEN_PREFIXES = (
    "data/raw/",
    "data/silver/",
    "data/research/",
    "data/gold/",
    "reports/backtests/",
    "reports/strategies/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
    ".git/",
    ".venv/",
)
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}
FORBIDDEN_SUFFIXES = {
    ".pyc",
    ".pkl",
    ".pickle",
    ".joblib",
    ".onnx",
    ".pt",
    ".pth",
    ".ckpt",
    ".zip",
    ".pem",
    ".key",
    ".sha256.json",
    ".sha256.txt",
}
ALLOWED_DECISIONS = {
    "resume_collection_completed_full_window",
    "resume_collection_partial_storage_warning",
    "resume_collection_partial_source_issue",
    "resume_collection_partial_quality_issue",
    "resume_collection_not_executed_storage_blocker",
    "resume_collection_not_executed_state_not_reconciled",
    "stop_aggtrades_completion_branch",
}


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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_25_1_audit_") as tmp:
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
    inventory = _read_json(extract_root / "reports/audit_lite/v9_25_1_artifact_inventory.json")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_25_1.json")
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
    report = _read_json(extract_root / "reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.json")
    manifest = _read_json(extract_root / "reports/manifests/aggtrades_post_v9_resume_campaign_v9_25_1_manifest.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_25_1_full_local_validation_attestation.json")
    summary = report.get("resume_summary", {})
    canonical = report.get("canonical_coverage_before_resume", {})
    decision = report.get("decision")
    if report.get("version") != VERSION or report.get("source_version") != "V9.25":
        errors.append("V9.25.1 report version/source mismatch")
    if report.get("correction_scope") != "campaign_state_reconciliation_and_resume_collection":
        errors.append("V9.25.1 correction_scope mismatch")
    if decision not in ALLOWED_DECISIONS:
        errors.append("V9.25.1 decision mismatch")
    if manifest.get("decision") != decision or manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.25.1 manifest mismatch")
    for raw_path in report.get("batch_report_paths", []):
        if raw_path not in _zip_manifest_files(extract_root):
            errors.append(f"V9.25.1 batch report not included in ZIP inventory: {raw_path}")
    if canonical.get("state_reconciled") is not True:
        errors.append("V9.25.1 canonical state must be reconciled")
    if canonical.get("first_missing_day") != "2025-02-03":
        errors.append("V9.25.1 must preserve first missing day before resume")
    if canonical.get("v9_25_reporting_inconsistency_detected") is not True:
        errors.append("V9.25.1 must document the V9.25 reporting inconsistency")
    disk = report.get("disk_preflight", {})
    if disk.get("minimum_free_bytes_required") != 60 * 1024**3:
        errors.append("V9.25.1 disk threshold mismatch")
    if decision == "resume_collection_partial_storage_warning":
        if summary.get("days_downloaded_total", 0) <= 0 or summary.get("days_complete_total", 0) <= 0:
            errors.append("V9.25.1 partial storage resume must preserve newly completed days")
        if summary.get("batches_executed", 0) < 1 or summary.get("batches_failed", 0) < 1:
            errors.append("V9.25.1 partial storage resume must expose the stopped batch")
        if summary.get("complete_collection_reached") is not False or summary.get("future_full_coverage_complete") is not False:
            errors.append("V9.25.1 partial storage resume must not claim full completion")
        if summary.get("local_file_coverage_end") == "2026-05-05":
            errors.append("V9.25.1 partial storage resume must not claim target end coverage")
    if decision == "resume_collection_completed_full_window":
        if summary.get("local_file_coverage_start") != "2024-05-05" or summary.get("local_file_coverage_end") != "2026-05-05":
            errors.append("V9.25.1 full completion coverage mismatch")
        if summary.get("complete_collection_reached") is not True or summary.get("future_full_coverage_complete") is not True:
            errors.append("V9.25.1 full completion flags mismatch")
    if summary.get("local_file_coverage_start") != "2024-05-05":
        errors.append("V9.25.1 local coverage start mismatch")
    if summary.get("days_quarantined_total", 0) != 0:
        errors.append("V9.25.1 resume must not quarantine days in delivered campaign")
    for key in ["total_rows_new", "raw_bytes_new", "silver_bytes_new"]:
        if report.get("collection_executed") and summary.get(key, 0) <= 0:
            errors.append(f"V9.25.1 {key} must be positive when collection executed")
    errors.extend(_check_flags(report, attestation))
    for payload_name, payload in {"report": report, "manifest": manifest, "attestation": attestation}.items():
        if _contains_forbidden_zip_field(payload):
            errors.append(f"{payload_name} contains forbidden ZIP fingerprint or sidecar field")
    return errors


def _check_flags(report: dict[str, Any], attestation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key in [
        "no_trading",
        "no_paper_live",
        "no_orders",
        "no_backtest",
        "no_walk_forward",
        "no_strategy",
        "no_actionable_signal",
        "no_persistent_model",
        "no_data_deletion",
        "no_destructive_cleanup",
        "no_sidecars",
        "no_zip_fingerprints",
    ]:
        if flags.get(key) is not True or attestation.get(key) is not True:
            errors.append(f"must confirm {key}=true")
    for key in ["api_key_used", "private_endpoint_used", "exchange_auth_used", "websocket_live_used"]:
        if flags.get(key) is not False or attestation.get(key) is not False:
            errors.append(f"must confirm {key}=false")
    if report.get("collection_executed"):
        if flags.get("network_used") is not True or flags.get("network_scope") != "public_archive_read_only":
            errors.append("collection must use public archive read-only network")
        if flags.get("new_data_downloaded") is not True or flags.get("new_data_download_scope") != "public_historical_aggtrades_resume_only":
            errors.append("download scope mismatch")
        if flags.get("ingestion_executed") is not True or flags.get("ingestion_scope") != "public_aggtrades_bronze_silver_resume_only":
            errors.append("ingestion scope mismatch")
    return errors


def _check_command_results(extract_root: Path) -> list[str]:
    errors: list[str] = []
    payload = _read_json(extract_root / "reports/audit_lite/v9_25_1_command_results.json")
    commands = payload.get("commands", [])
    if payload.get("version") != VERSION:
        errors.append("command_results version mismatch")
    if not commands:
        return ["command_results must contain executed commands"]
    for needle in [
        "pytest --collect-only -q",
        "test_aggtrades_post_v9_resume_campaign_v9_25_1.py",
        "test_aggtrades_post_v9_resume_campaign_v9_25_1_validator.py",
        "run_aggtrades_post_v9_resume_campaign_v9_25_1.py",
        "validate_aggtrades_post_v9_resume_campaign_v9_25_1.py",
        "release_audit_lite_zip_v9_25_1.py",
    ]:
        if not any(needle in item.get("command", "") and item.get("status") == "PASS" for item in commands):
            errors.append(f"command_results missing PASS command containing: {needle}")
    failed = [item.get("command") for item in commands if item.get("status") == "FAIL"]
    if failed:
        errors.append(f"command_results contains failed commands: {failed}")
    return errors


def _check_state(extract_root: Path) -> list[str]:
    errors: list[str] = []
    state = _read_json(extract_root / "reports/PROJECT_STATE.json")
    metrics = _read_json(extract_root / "reports/current/latest_metrics.json")
    for name, payload in {"PROJECT_STATE": state, "latest_metrics": metrics}.items():
        if payload.get("last_validated_version") != "V9.25":
            errors.append(f"{name} last_validated_version mismatch")
        if payload.get("candidate_version") != VERSION:
            errors.append(f"{name} candidate_version mismatch")
        if payload.get("candidate_status") != "pending_external_audit":
            errors.append(f"{name} candidate_status mismatch")
        if payload.get("direction") != "aggtrades_post_v9_resume_collection":
            errors.append(f"{name} direction mismatch")
    return errors


def _zip_manifest_files(extract_root: Path) -> set[str]:
    inventory = _read_json(extract_root / "reports/audit_lite/v9_25_1_artifact_inventory.json")
    return set(inventory.get("files", []))


def _is_forbidden(name: str) -> bool:
    path = Path(name)
    if name.startswith(FORBIDDEN_PREFIXES):
        return True
    if any(part in FORBIDDEN_PARTS for part in path.parts):
        return True
    if path.name in FORBIDDEN_NAMES:
        return True
    return any(name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            text = str(key).casefold()
            if text == "zip_sha256" or text.startswith("sidecar_"):
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
    (report_dir / "zip_audit_v9_25_1.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_25_1.md").write_text(
        "# Audit ZIP V9.25.1\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
