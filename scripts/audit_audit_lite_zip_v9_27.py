from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.27"
ZIP_NAME = "projet-galapagos-v9.27-audit-lite.zip"
REQUIRED_FILES = [
    "scripts/_bootstrap.py",
    "scripts/run_aggtrades_post_v9_storage_recheck_resume_v9_27.py",
    "scripts/validate_aggtrades_post_v9_storage_recheck_resume_v9_27.py",
    "scripts/release_audit_lite_zip_v9_27.py",
    "scripts/audit_audit_lite_zip_v9_27.py",
    "scripts/smoke_audit_lite_zip_v9_27.py",
    "src/galapagos/data/aggtrades_post_v9_storage_recheck_resume_v9_27.py",
    "src/galapagos/data/aggtrades_post_v9_storage_recheck_resume_v9_27_validation.py",
    "tests/data/test_aggtrades_post_v9_storage_recheck_resume_v9_27.py",
    "tests/validation/test_aggtrades_post_v9_storage_recheck_resume_v9_27_validator.py",
    "reports/manifests/aggtrades_post_v9_storage_recheck_resume_v9_27_manifest.json",
    "reports/data/aggtrades_post_v9_storage_recheck_resume_v9_27.json",
    "reports/data/aggtrades_post_v9_storage_recheck_resume_v9_27.md",
    "docs/aggtrades_post_v9_storage_recheck_resume_v9_27.md",
    "reports/audit_lite/v9_27_command_results.json",
    "reports/audit_lite/v9_27_command_results.md",
    "reports/audit_lite/v9_27_full_local_validation_attestation.json",
    "reports/audit_lite/v9_27_full_local_validation_attestation.md",
    "reports/audit_lite/v9_27_artifact_inventory.json",
    "reports/audit_lite/v9_27_artifact_inventory.md",
    "reports/audit_lite/zip_size_report_v9_27.json",
    "reports/audit_lite/zip_size_report_v9_27.md",
    "reports/audit_lite/zip_audit_v9_27.json",
    "reports/audit_lite/zip_audit_v9_27.md",
    "reports/audit_lite/zip_smoke_v9_27.json",
    "reports/audit_lite/zip_smoke_v9_27.md",
    "reports/data/aggtrades_post_v9_storage_resume_campaign_v9_26.json",
    "reports/manifests/aggtrades_post_v9_storage_resume_campaign_v9_26_manifest.json",
    "reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.json",
    "reports/data/aggtrades_post_v9_completion_campaign_v9_25.json",
    "reports/data/aggtrades_post_v9_batch3_collection_v9_24.json",
    "reports/data/aggtrades_post_v9_batch2_collection_v9_23.json",
    "reports/data/aggtrades_post_v9_batch_expansion_v9_21.json",
    "reports/data/aggtrades_post_v9_batch_collection_v9_20.json",
    "reports/data/aggtrades_post_v9_pilot_collection_v9_19.json",
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
    if not zipfile.is_zipfile(zip_path):
        return [f"not a valid zip: {zip_path}"]
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_27_audit_") as tmp:
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
    inventory = _read_json(extract_root / "reports/audit_lite/v9_27_artifact_inventory.json")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_27.json")
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
    report = _read_json(extract_root / "reports/data/aggtrades_post_v9_storage_recheck_resume_v9_27.json")
    manifest = _read_json(extract_root / "reports/manifests/aggtrades_post_v9_storage_recheck_resume_v9_27_manifest.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_27_full_local_validation_attestation.json")
    summary = report.get("storage_recheck_summary", {})
    disk = report.get("disk_preflight", {})
    if report.get("version") != VERSION or report.get("source_version") != "V9.26":
        errors.append("V9.27 report version/source mismatch")
    if report.get("decision") not in {
        "storage_recheck_resume_completed_full_window",
        "storage_recheck_resume_partial_storage_warning",
        "storage_recheck_resume_partial_source_issue",
        "storage_recheck_resume_partial_quality_issue",
        "storage_recheck_not_executed_storage_blocker",
        "storage_recheck_not_executed_measurement_discrepancy",
        "storage_recheck_not_executed_state_not_reconciled",
        "stop_aggtrades_completion_branch",
    }:
        errors.append("V9.27 decision is not allowed")
    if manifest.get("decision") != report.get("decision") or manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.27 manifest mismatch")
    if disk.get("data_mount_path") != disk.get("project_mount_path"):
        errors.append("V9.27 project and data mount should be explicit and matched for this repo")
    if summary.get("local_file_coverage_start") != "2024-05-05":
        errors.append("V9.27 local coverage must start at target start")
    if report.get("decision") != "storage_recheck_resume_completed_full_window":
        coverage_end = summary.get("local_file_coverage_end")
        if coverage_end is not None and not ("2025-02-03" <= coverage_end <= "2026-05-05"):
            errors.append("V9.27 partial local coverage end is outside the target range")
    if report.get("decision") == "storage_recheck_resume_completed_full_window":
        if summary.get("local_file_coverage_start") != "2024-05-05" or summary.get("local_file_coverage_end") != "2026-05-05":
            errors.append("V9.27 completed decision must cover the full target window")
        if summary.get("complete_collection_reached") is not True or summary.get("future_full_coverage_complete") is not True:
            errors.append("V9.27 completed decision must set full completion flags")
        if summary.get("days_downloaded_total", 0) <= 0 or summary.get("days_normalized_total", 0) <= 0:
            errors.append("V9.27 completed decision must download and normalize public aggTrades")
    if report.get("decision") in {"storage_recheck_not_executed_storage_blocker", "storage_recheck_not_executed_measurement_discrepancy", "storage_recheck_not_executed_state_not_reconciled"}:
        if summary.get("days_downloaded_total") != 0 or summary.get("days_normalized_total") != 0 or summary.get("days_complete_total") != 0:
            errors.append("V9.27 not-executed decision must not download, normalize or complete new days")
        if summary.get("complete_collection_reached") is not False or summary.get("future_full_coverage_complete") is not False:
            errors.append("V9.27 not-executed decision must not claim full completion")
    errors.extend(_check_flags(report, attestation))
    for payload_name, payload in {"report": report, "manifest": manifest, "attestation": attestation}.items():
        if _contains_forbidden_zip_field(payload):
            errors.append(f"{payload_name} contains forbidden ZIP fingerprint or sidecar field")
    return errors


def _check_flags(report: dict[str, Any], attestation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key in ["no_trading", "no_paper_live", "no_orders", "no_backtest", "no_walk_forward", "no_strategy", "no_actionable_signal", "no_persistent_model", "no_data_deletion", "no_destructive_cleanup", "no_sidecars", "no_zip_fingerprints"]:
        if flags.get(key) is not True or attestation.get(key) is not True:
            errors.append(f"must confirm {key}=true")
    for key in ["api_key_used", "private_endpoint_used", "exchange_auth_used", "websocket_live_used"]:
        if flags.get(key) is not False or attestation.get(key) is not False:
            errors.append(f"must confirm {key}=false")
    if report.get("collection_executed"):
        if flags.get("network_used") is not True or attestation.get("network_used") is not True:
            errors.append("collection must confirm network_used=true")
        if flags.get("new_data_downloaded") is not True or attestation.get("new_data_downloaded") is not True:
            errors.append("collection must confirm new_data_downloaded=true")
        if flags.get("ingestion_executed") is not True or attestation.get("ingestion_executed") is not True:
            errors.append("collection must confirm ingestion_executed=true")
        if flags.get("network_scope") != "public_archive_read_only":
            errors.append("collection must use public_archive_read_only network scope")
    else:
        for key in ["network_used", "new_data_downloaded", "ingestion_executed"]:
            if flags.get(key) is not False or attestation.get(key) is not False:
                errors.append(f"must confirm {key}=false")
        if flags.get("no_new_data_download") is not True or flags.get("no_ingestion_executed") is not True:
            errors.append("must confirm no new data download and no ingestion")
    return errors


def _check_command_results(extract_root: Path) -> list[str]:
    payload = _read_json(extract_root / "reports/audit_lite/v9_27_command_results.json")
    commands = payload.get("commands", [])
    errors: list[str] = []
    if payload.get("version") != VERSION:
        errors.append("command_results version mismatch")
    if not commands:
        return ["command_results must contain executed commands"]
    for needle in [
        "df -h /Users/lilianserre/Documents/projets/projet-galapagos",
        "pytest --collect-only -q",
        "test_aggtrades_post_v9_storage_recheck_resume_v9_27.py",
        "test_aggtrades_post_v9_storage_recheck_resume_v9_27_validator.py",
        "run_aggtrades_post_v9_storage_recheck_resume_v9_27.py",
        "validate_aggtrades_post_v9_storage_recheck_resume_v9_27.py",
        "release_audit_lite_zip_v9_27.py",
    ]:
        if not any(needle in item.get("command", "") and item.get("status") == "PASS" for item in commands):
            errors.append(f"command_results missing PASS command containing: {needle}")
    return errors


def _check_state(extract_root: Path) -> list[str]:
    errors: list[str] = []
    state = _read_json(extract_root / "reports/PROJECT_STATE.json")
    metrics = _read_json(extract_root / "reports/current/latest_metrics.json")
    for name, payload in {"PROJECT_STATE": state, "latest_metrics": metrics}.items():
        if payload.get("last_validated_version") != "V9.26":
            errors.append(f"{name} last_validated_version mismatch")
        if payload.get("candidate_version") != VERSION:
            errors.append(f"{name} candidate_version mismatch")
        if payload.get("candidate_status") != "pending_external_audit":
            errors.append(f"{name} candidate_status mismatch")
        if payload.get("direction") != "aggtrades_post_v9_storage_recheck_resume":
            errors.append(f"{name} direction mismatch")
    return errors


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
    (report_dir / "zip_audit_v9_27.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_27.md").write_text(
        "# Audit ZIP V9.27\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
