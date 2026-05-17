from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V_DISP = "V1.83"
V_NORM = "v1_83"
EXPECTED_SCOPE = "tiny_data_contract_materialization_ultra_bounded_no_network_no_full_dataset_no_ml_no_trading"


REQUIRED_JSON = {
    "summary": f"reports/research/microstructure_data_contract_approval_gate_summary_{V_NORM}.json",
    "decision": f"reports/research/microstructure_data_contract_approval_gate_decision_{V_NORM}.json",
    "safety": f"reports/research/microstructure_data_contract_approval_gate_safety_check_{V_NORM}.json",
    "consistency": f"reports/research/microstructure_data_contract_approval_gate_consistency_check_{V_NORM}.json",
    "latest": "reports/current/latest_metrics.json",
    "project": "reports/PROJECT_STATE.json",
    "release": f"reports/release_zip_{V_NORM}.json",
    "audit": f"reports/zip_audit_{V_NORM}.json",
    "smoke": f"reports/zip_smoke_test_{V_NORM}.json",
}


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "approval_gate_only": True,
        "reports_only": True,
        "v1_84_execution_attempted": False,
        "materialization_executed": False,
        "data_contract_actual_write_executed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "dataset_created": False,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "ml_signal_validation_executed": False,
    }
    for field, value in expected.items():
        if payload.get(field) is not value:
            errors.append(f"{field} != {value!r}")
    if payload.get("approval_phrase_match") is False and payload.get("human_approval_granted") is True:
        errors.append("approval granted despite phrase mismatch")
    if payload.get("human_approval_granted") is True:
        if payload.get("authorized_future_version") != "V1.84":
            errors.append("authorized_future_version must be V1.84")
        if payload.get("authorized_future_scope") != EXPECTED_SCOPE:
            errors.append("authorized_future_scope mismatch")
    if payload.get("release_ready_for_external_review") is not True:
        errors.append("release_ready_for_external_review != true")
    if payload.get("smoke_test_passed") is not True:
        errors.append("smoke_test_passed != true")
    if payload.get("clean_zip_ready_for_external_review") is not True:
        errors.append("clean_zip_ready_for_external_review != true")
    return errors


def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_report_set(root: Path = PROJECT_ROOT) -> list[str]:
    errors: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    for key, rel in REQUIRED_JSON.items():
        path = root / rel
        if not path.exists():
            errors.append(f"missing {rel}")
            continue
        loaded[key] = _load(path)
        if path.with_suffix(".md").exists() is False:
            errors.append(f"missing markdown {path.with_suffix('.md').relative_to(root)}")
    for rel in ["reports/REPORT_INDEX.md", "docs/code_review_v1_83.md", "docs/microstructure_data_contract_approval_gate_v1_83.md"]:
        if not (root / rel).exists():
            errors.append(f"missing {rel}")
    if errors:
        return errors

    for key, payload in loaded.items():
        if payload.get("version") != V_DISP:
            errors.append(f"{key}: version mismatch {payload.get('version')!r}")
    summary = loaded["summary"]
    errors.extend(f"summary: {e}" for e in validate_payload(summary))
    for source in ["latest", "project"]:
        for field in [
            "version",
            "final_verdict",
            "approval_phrase_match",
            "human_approval_granted",
            "v1_84_authorized",
            "authorized_future_scope",
            "v1_84_execution_attempted",
            "materialization_executed",
            "data_contract_actual_write_executed",
            "data_directory_write_attempted",
            "new_data_files_created",
            "dataset_created",
            "network_executed",
            "trading_allowed",
            "real_orders_possible",
            "release_ready_for_external_review",
            "clean_zip_ready_for_external_review",
            "smoke_test_passed",
            "blocking_reason",
        ]:
            if loaded[source].get(field) != summary.get(field):
                errors.append(f"{source}: {field} diverges from summary")
    release = loaded["release"]
    if release.get("release_ready_for_external_review") is not True:
        errors.append("release: release_ready_for_external_review != true")
    if release.get("clean_zip_ready_for_external_review") is not True:
        errors.append("release: clean_zip_ready_for_external_review != true")
    if release.get("blocking_reason") is not None:
        errors.append("release: blocking_reason != null")
    smoke = loaded["smoke"]
    if smoke.get("smoke_test_passed") is not True:
        errors.append("smoke: smoke_test_passed != true")
    if smoke.get("smoke_failed_count") != 0:
        errors.append("smoke: smoke_failed_count != 0")
    audit = loaded["audit"]
    if audit.get("clean_zip_ready_for_external_review") is not True:
        errors.append("audit: clean_zip_ready_for_external_review != true")
    index = (root / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    if "v1_83" not in index or "V1.83" not in index:
        errors.append("REPORT_INDEX does not reference V1.83")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=V_NORM)
    args = parser.parse_args()
    if args.version != V_NORM:
        raise SystemExit(f"Unsupported version: {args.version}")
    errors = validate_report_set(PROJECT_ROOT)
    if errors:
        print("FAIL: V1.83 validation failed")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print("PASS: V1.83 approval gate reports validated.")


if __name__ == "__main__":
    main()
