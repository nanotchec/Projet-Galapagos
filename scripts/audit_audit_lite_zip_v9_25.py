from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.25"
ZIP_NAME = "projet-galapagos-v9.25-audit-lite.zip"

BATCH_REPORTS = [f"reports/data/aggtrades_post_v9_completion_batch{index:02d}_v9_25.json" for index in range(1, 7)]

REQUIRED_FILES = [
    "scripts/_bootstrap.py",
    "scripts/run_aggtrades_post_v9_completion_campaign_v9_25.py",
    "scripts/validate_aggtrades_post_v9_completion_campaign_v9_25.py",
    "scripts/release_audit_lite_zip_v9_25.py",
    "scripts/audit_audit_lite_zip_v9_25.py",
    "scripts/smoke_audit_lite_zip_v9_25.py",
    "src/galapagos/data/aggtrades_post_v9_collection_v9_18.py",
    "src/galapagos/data/aggtrades_post_v9_batch3_collection_v9_24.py",
    "src/galapagos/data/aggtrades_post_v9_completion_campaign_v9_25.py",
    "src/galapagos/data/aggtrades_post_v9_completion_campaign_v9_25_validation.py",
    "tests/data/test_aggtrades_post_v9_completion_campaign_v9_25.py",
    "tests/validation/test_aggtrades_post_v9_completion_campaign_v9_25_validator.py",
    *BATCH_REPORTS,
    "reports/manifests/aggtrades_post_v9_completion_campaign_v9_25_manifest.json",
    "reports/data/aggtrades_post_v9_completion_campaign_v9_25.json",
    "reports/data/aggtrades_post_v9_completion_campaign_v9_25.md",
    "docs/aggtrades_post_v9_completion_campaign_v9_25.md",
    "reports/audit_lite/v9_25_command_results.json",
    "reports/audit_lite/v9_25_command_results.md",
    "reports/audit_lite/v9_25_full_local_validation_attestation.json",
    "reports/audit_lite/v9_25_full_local_validation_attestation.md",
    "reports/audit_lite/v9_25_artifact_inventory.json",
    "reports/audit_lite/v9_25_artifact_inventory.md",
    "reports/audit_lite/zip_size_report_v9_25.json",
    "reports/audit_lite/zip_size_report_v9_25.md",
    "reports/audit_lite/zip_audit_v9_25.json",
    "reports/audit_lite/zip_audit_v9_25.md",
    "reports/audit_lite/zip_smoke_v9_25.json",
    "reports/audit_lite/zip_smoke_v9_25.md",
    "reports/data/aggtrades_post_v9_batch3_collection_v9_24.json",
    "reports/manifests/aggtrades_post_v9_batch3_collection_v9_24_manifest.json",
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

FORBIDDEN_PREFIXES = [
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
]
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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_25_audit_") as tmp:
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
    inventory = _read_json(extract_root / "reports/audit_lite/v9_25_artifact_inventory.json")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_25.json")
    if inventory.get("zip_name") != ZIP_NAME:
        errors.append("inventory zip_name mismatch")
    if inventory.get("files_count") != len(names) or sorted(inventory.get("files", [])) != names:
        errors.append("inventory files do not match ZIP content")
    for payload_name, payload in {"inventory": inventory, "size_report": size_report}.items():
        if not isinstance(payload.get("zip_bytes_estimate"), int) or payload.get("zip_bytes_estimate", 0) <= 0:
            errors.append(f"{payload_name} must contain a positive zip_bytes_estimate")
        if payload.get("zip_bytes_is_authoritative") is not False:
            errors.append(f"{payload_name} must mark zip_bytes_is_authoritative=false")
        if _contains_forbidden_zip_field(payload):
            errors.append(f"{payload_name} contains forbidden ZIP hash or sidecar field")
        if payload.get("sidecars_created") is not False or payload.get("zip_fingerprints_created") is not False:
            errors.append(f"{payload_name} must confirm no sidecars and no fingerprints")
    for key, value in inventory.get("forbidden_absences_verified", {}).items():
        if value is not True:
            errors.append(f"forbidden absence failed: {key}")
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    report = _read_json(extract_root / "reports/data/aggtrades_post_v9_completion_campaign_v9_25.json")
    manifest = _read_json(extract_root / "reports/manifests/aggtrades_post_v9_completion_campaign_v9_25_manifest.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_25_full_local_validation_attestation.json")
    summary = report.get("campaign_summary", {})
    decision = report.get("decision")
    if decision not in {
        "aggtrades_post_v9_remaining_window_collection_complete",
        "aggtrades_post_v9_remaining_window_collection_failed_storage",
    }:
        errors.append("V9.25 decision mismatch")
    if summary.get("batches_planned") != 6:
        errors.append("V9.25 must report six planned internal batches")
    if decision == "aggtrades_post_v9_remaining_window_collection_complete":
        if summary.get("batches_executed") != 6 or summary.get("batches_complete") != 6 or summary.get("batches_failed") != 0:
            errors.append("V9.25 complete campaign must report six executed/complete batches and zero failures")
        if summary.get("days_requested_total") != 514 or summary.get("days_attempted_total") != 514:
            errors.append("V9.25 requested/attempted day counts mismatch")
        if summary.get("days_downloaded_total") != 514 or summary.get("days_normalized_total") != 514 or summary.get("days_complete_total") != 514:
            errors.append("V9.25 complete campaign must report 514 downloaded/normalized/complete days")
        if summary.get("days_failed_total") != 0 or summary.get("days_quarantined_total") != 0:
            errors.append("V9.25 complete campaign must report no failed or quarantined days")
        if summary.get("local_file_coverage_end") != "2026-05-05" or summary.get("complete_collection_reached") is not True:
            errors.append("V9.25 complete campaign coverage mismatch")
    if decision == "aggtrades_post_v9_remaining_window_collection_failed_storage":
        if summary.get("batches_executed") != 1 or summary.get("batches_complete") != 0 or summary.get("batches_failed") != 1:
            errors.append("V9.25 storage stop must report one evaluated failed batch")
        if summary.get("days_complete_total", 0) <= 0:
            errors.append("V9.25 storage stop should preserve partial local coverage metrics")
        if summary.get("days_quarantined_total") != 0:
            errors.append("V9.25 storage stop must not quarantine days")
        if summary.get("complete_collection_reached") is not False or summary.get("future_full_coverage_complete") is not False:
            errors.append("V9.25 storage stop must not claim full completion")
        if summary.get("local_file_coverage_end") == "2026-05-05":
            errors.append("V9.25 storage stop must not claim target end coverage")
    for key in ["total_rows_new", "total_rows_cumulative", "raw_bytes_new", "silver_bytes_new", "raw_bytes_cumulative", "silver_bytes_cumulative"]:
        if summary.get(key, 0) <= 0:
            errors.append(f"V9.25 {key} must be positive")
    if summary.get("local_file_coverage_start") != "2024-05-05":
        errors.append("V9.25 local coverage mismatch")
    if summary.get("reported_cumulative_coverage_start") != "2024-05-05" or summary.get("reported_cumulative_coverage_end") != summary.get("local_file_coverage_end"):
        errors.append("V9.25 reported coverage mismatch")
    if not isinstance(summary.get("aggregate_trade_id_gap_warnings"), list) or not isinstance(summary.get("timestamp_gap_warnings"), list):
        errors.append("V9.25 warning lists must be present")
    for index, raw_path in enumerate(BATCH_REPORTS, start=1):
        batch_report = _read_json(extract_root / raw_path)
        batch_summary = batch_report.get("batch_summary", {})
        if decision == "aggtrades_post_v9_remaining_window_collection_complete" and batch_summary.get("batch_success") is not True:
            errors.append(f"internal batch not successful: {raw_path}")
        if decision == "aggtrades_post_v9_remaining_window_collection_failed_storage":
            if index == 1 and batch_summary.get("failure_type") != "storage":
                errors.append("first internal batch must carry storage failure_type")
            if index > 1 and batch_report.get("status") != "NOT_EXECUTED":
                errors.append(f"later internal batch must be NOT_EXECUTED after storage stop: {raw_path}")
    if manifest.get("decision") != report.get("decision"):
        errors.append("V9.25 manifest decision mismatch")
    for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced", "walk_forward_validated_for_trading"]:
        if report.get("findings", {}).get(key) is not False:
            errors.append(f"finding must be false: {key}")
    for key in ["no_trading", "no_paper_live", "no_orders", "no_backtest", "no_walk_forward", "no_strategy", "no_actionable_signal", "no_persistent_model", "no_sidecars", "no_zip_fingerprints"]:
        if attestation.get(key) is not True:
            errors.append(f"attestation must confirm {key}=true")
    for key in ["api_key_used", "private_endpoint_used", "exchange_auth_used", "websocket_live_used"]:
        if attestation.get(key) is not False:
            errors.append(f"attestation must confirm {key}=false")
    if attestation.get("network_used") is not True or attestation.get("no_new_data_download") is not False or attestation.get("no_ingestion_executed") is not False:
        errors.append("attestation must confirm public network, new download and ingestion")
    for payload_name, payload in {"report": report, "manifest": manifest, "attestation": attestation}.items():
        if _contains_forbidden_zip_field(payload):
            errors.append(f"{payload_name} contains forbidden ZIP hash or sidecar field")
    return errors


def _check_command_results(extract_root: Path) -> list[str]:
    errors: list[str] = []
    payload = _read_json(extract_root / "reports/audit_lite/v9_25_command_results.json")
    commands = payload.get("commands", [])
    if payload.get("version") != VERSION:
        errors.append("command_results version mismatch")
    if not commands:
        errors.append("command_results must contain executed commands")
        return errors
    required_needles = [
        "pytest --collect-only -q",
        "test_aggtrades_post_v9_completion_campaign_v9_25.py",
        "test_aggtrades_post_v9_completion_campaign_v9_25_validator.py",
        "run_aggtrades_post_v9_completion_campaign_v9_25.py",
        "validate_aggtrades_post_v9_completion_campaign_v9_25.py",
        "release_audit_lite_zip_v9_25.py",
    ]
    for needle in required_needles:
        if not any(needle in item.get("command", "") and item.get("status") == "PASS" for item in commands):
            errors.append(f"command_results missing PASS command containing: {needle}")
    return errors


def _check_state(extract_root: Path) -> list[str]:
    errors: list[str] = []
    state = _read_json(extract_root / "reports/PROJECT_STATE.json")
    metrics = _read_json(extract_root / "reports/current/latest_metrics.json")
    for name, payload in {"PROJECT_STATE": state, "latest_metrics": metrics}.items():
        if payload.get("last_validated_version") != "V9.24":
            errors.append(f"{name} last_validated_version mismatch")
        if payload.get("candidate_version") != VERSION:
            errors.append(f"{name} candidate_version mismatch")
        if payload.get("candidate_status") != "pending_external_audit":
            errors.append(f"{name} candidate_status mismatch")
        if payload.get("direction") != "aggtrades_post_v9_remaining_window_completion_campaign":
            errors.append(f"{name} direction mismatch")
        decision = payload.get("v9_25_decision")
        if decision == "aggtrades_post_v9_remaining_window_collection_complete":
            if payload.get("complete_collection_reached") is not True:
                errors.append(f"{name} must confirm complete collection reached")
        elif decision == "aggtrades_post_v9_remaining_window_collection_failed_storage":
            if payload.get("complete_collection_reached") is not False or payload.get("future_full_coverage_complete") is not False:
                errors.append(f"{name} must confirm storage stop without complete collection")
        else:
            errors.append(f"{name} V9.25 decision mismatch")
        if payload.get("no_sidecars") is not True or payload.get("no_zip_fingerprints") is not True:
            errors.append(f"{name} must confirm no sidecars and no ZIP fingerprints")
        if payload.get("api_key_used") is not False or payload.get("private_endpoint_used") is not False:
            errors.append(f"{name} must confirm no API key and no private endpoint")
        if payload.get("exchange_auth_used") is not False or payload.get("websocket_live_used") is not False:
            errors.append(f"{name} must confirm no exchange auth and no websocket live")
        if payload.get("network_used") is not True or payload.get("no_new_data_download") is not False or payload.get("no_ingestion_executed") is not False:
            errors.append(f"{name} must confirm public network, new download and ingestion")
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
    if isinstance(payload, list):
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
    (report_dir / "zip_audit_v9_25.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_25.md").write_text(
        "# Audit ZIP V9.25\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
