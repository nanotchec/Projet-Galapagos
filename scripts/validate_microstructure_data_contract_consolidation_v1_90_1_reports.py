from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from galapagos.research.microstructure_data_contract_consolidation.validator import validate_payload  # noqa: E402
from galapagos.research.microstructure_data_contract_consolidation_readiness.physical_auditor import (  # noqa: E402
    EXPECTED_V1_84_HASHES,
    EXPECTED_V1_87_HASHES,
    V1_84_DATA_ROOT,
    V1_87_DATA_ROOT,
)

V_DISP = "V1.90.1"
V_NORM = "v1_90_1"
V1_90_ROOT = Path("data/research/microstructure_contract_materialization/v1_90")
V1_90_FILES = [
    V1_90_ROOT / "consolidated_manifest.json",
    V1_90_ROOT / "consolidated_schema_snapshot.json",
    V1_90_ROOT / "consolidated_quality_summary.json",
]
REQUIRED_PATHS = {
    "summary": f"reports/research/microstructure_data_contract_consolidation_summary_{V_NORM}.json",
    "file": f"reports/research/microstructure_data_contract_consolidation_file_audit_{V_NORM}.json",
    "safety": f"reports/research/microstructure_data_contract_consolidation_safety_check_{V_NORM}.json",
    "consistency": f"reports/research/microstructure_data_contract_consolidation_consistency_check_{V_NORM}.json",
    "latest": "reports/current/latest_metrics.json",
    "project": "reports/PROJECT_STATE.json",
    "latest_summary": "reports/current/latest_summary.md",
    "index": "reports/REPORT_INDEX.md",
    "release": f"reports/release_zip_{V_NORM}.json",
    "audit": f"reports/zip_audit_{V_NORM}.json",
    "smoke": f"reports/zip_smoke_test_{V_NORM}.json",
    "code_review": "docs/code_review_v1_90_1.md",
    "doc": "docs/microstructure_data_contract_consolidation_v1_90_1.md",
}
CRITICAL_FIELDS = [
    "version", "final_verdict", "approval_source_verified", "human_approval_granted", "v1_90_authorized",
    "consolidation_executed", "tiny_consolidation_only", "full_dataset_created", "network_executed",
    "new_network_requests_executed", "data_directory_writes_allowed", "data_write_approved",
    "data_directory_write_attempted", "new_data_files_created", "consolidation_actual_write_executed",
    "unapproved_data_write_detected", "total_new_data_files_created", "created_files_count",
    "total_data_bytes_written", "existing_v1_84_files_modified", "existing_v1_87_files_modified",
    "parquet_created", "csv_created", "sqlite_created", "jsonl_created", "db_created", "dataset_created",
    "research_dataset_updated", "trading_allowed", "real_orders_possible", "no_real_trading", "no_paper_live",
    "ml_signal_validation_executed", "predictions_created", "labels_created", "targets_created",
    "pytest_executed", "pytest_exit_code", "pytest_failed_count", "release_ready_for_external_review",
    "clean_zip_ready_for_external_review", "smoke_test_passed", "blocking_reason",
]


def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _json_valid(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return True
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False


def _strict_release(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_true = [
        "release_zip_created", "final_zip_created", "release_ready_for_external_review",
        "clean_zip_ready_for_external_review", "final_audit_passed", "final_smoke_passed",
    ]
    for field in expected_true:
        if payload.get(field) is not True:
            errors.append(f"release: {field} != true")
    if payload.get("blocking_reason") is not None:
        errors.append("release: blocking_reason != null")
    if payload.get("version") != V_DISP:
        errors.append("release: version mismatch")
    return errors


def _strict_audit(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("version") != V_DISP:
        errors.append("audit: version mismatch")
    if payload.get("clean_zip_ready_for_external_review") is not True:
        errors.append("audit: clean_zip_ready_for_external_review != true")
    if payload.get("audit_zip_project_state_version") != V_DISP:
        errors.append("audit: audit_zip_project_state_version mismatch")
    if payload.get("audit_zip_version_parse_correct") is not True:
        errors.append("audit: audit_zip_version_parse_correct != true")
    if payload.get("forbidden_count") != 0:
        errors.append("audit: forbidden_count != 0")
    if payload.get("missing_required_files") != []:
        errors.append("audit: missing_required_files != []")
    if payload.get("global_json_finiteness_passed") is not True:
        errors.append("audit: global_json_finiteness_passed != true")
    return errors


def _strict_smoke(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("version") != V_DISP:
        errors.append("smoke: version mismatch")
    if payload.get("smoke_test_passed") is not True:
        errors.append("smoke: smoke_test_passed != true")
    if payload.get("smoke_failed_count") != 0:
        errors.append("smoke: smoke_failed_count != 0")
    if payload.get("smoke_passed_count") != payload.get("smoke_commands_count"):
        errors.append("smoke: smoke_passed_count != smoke_commands_count")
    if payload.get("smoke_commands_not_empty") is not True:
        errors.append("smoke: smoke_commands_not_empty != true")
    if payload.get("real_orders_possible") is not False:
        errors.append("smoke: real_orders_possible != false")
    if payload.get("codex_cli_called") is not False:
        errors.append("smoke: codex_cli_called != false")
    if payload.get("holdout_executed") is not False:
        errors.append("smoke: holdout_executed != false")
    return errors


def _physical_checks(root: Path, file_audit: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    v1_90_root = root / V1_90_ROOT
    allowed = {root / path for path in V1_90_FILES}
    existing = sorted(path for path in v1_90_root.glob("*") if path.is_file()) if v1_90_root.exists() else []
    if set(existing) != allowed:
        errors.append("physical: V1.90 folder does not contain exactly the three authorized files")
    for path in allowed:
        if not path.exists():
            errors.append(f"physical: missing {path.relative_to(root)}")
        elif not _json_valid(path):
            errors.append(f"physical: invalid JSON {path.relative_to(root)}")
    for path in existing:
        if path.suffix.lower() in {".parquet", ".csv", ".sqlite", ".jsonl", ".db"}:
            errors.append(f"physical: forbidden file type {path.relative_to(root)}")
    v1_84_hashes = {name: _sha256(root / V1_84_DATA_ROOT / name) for name in EXPECTED_V1_84_HASHES}
    v1_87_hashes = {name: _sha256(root / V1_87_DATA_ROOT / name) for name in EXPECTED_V1_87_HASHES}
    if v1_84_hashes != EXPECTED_V1_84_HASHES:
        errors.append("physical: V1.84 hash mismatch")
    if v1_87_hashes != EXPECTED_V1_87_HASHES:
        errors.append("physical: V1.87 hash mismatch")
    if file_audit.get("v1_84_hashes_observed") != v1_84_hashes:
        errors.append("file_audit: V1.84 hashes do not match physical files")
    if file_audit.get("v1_87_hashes_observed") != v1_87_hashes:
        errors.append("file_audit: V1.87 hashes do not match physical files")
    return errors


def validate_report_set(root: Path = PROJECT_ROOT) -> list[str]:
    errors: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    for key, rel in REQUIRED_PATHS.items():
        path = root / rel
        if not path.exists():
            errors.append(f"missing {rel}")
            continue
        if path.suffix == ".json":
            loaded[key] = _load(path)
            if not path.with_suffix(".md").exists() and key in {"summary", "file", "safety", "consistency"}:
                errors.append(f"missing markdown {path.with_suffix('.md').relative_to(root)}")
    if errors:
        return errors
    summary = loaded["summary"]
    latest = loaded["latest"]
    project = loaded["project"]
    errors.extend(validate_payload(summary))
    for field in CRITICAL_FIELDS:
        if field not in summary:
            errors.append(f"summary missing critical field {field}")
        if field not in latest:
            errors.append(f"latest missing critical field {field}")
        if field not in project:
            errors.append(f"project missing critical field {field}")
        if field in summary and latest.get(field) != summary.get(field):
            errors.append(f"latest: {field} diverges from summary")
        if field in summary and project.get(field) != summary.get(field):
            errors.append(f"project: {field} diverges from summary")
    if summary.get("version") != V_DISP:
        errors.append("summary: version mismatch")
    errors.extend(_strict_release(loaded["release"]))
    errors.extend(_strict_audit(loaded["audit"]))
    errors.extend(_strict_smoke(loaded["smoke"]))
    errors.extend(_physical_checks(root, loaded["file"]))
    index = (root / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    if "v1_90_1" not in index or "V1.90.1" not in index:
        errors.append("REPORT_INDEX does not reference V1.90.1")
    latest_summary = (root / "reports/current/latest_summary.md").read_text(encoding="utf-8")
    if "V1.90.1" not in latest_summary:
        errors.append("latest_summary does not mention V1.90.1")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=V_NORM)
    args = parser.parse_args()
    if args.version != V_NORM:
        raise SystemExit(f"Unsupported version: {args.version}")
    errors = validate_report_set(PROJECT_ROOT)
    if errors:
        print("FAIL: V1.90.1 validation failed")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print("PASS: V1.90.1 strict consolidation reports validated.")


if __name__ == "__main__":
    main()
