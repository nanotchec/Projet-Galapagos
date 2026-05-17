from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from galapagos.research.microstructure_data_contract_consolidation_readiness import (  # noqa: E402
    AUTHORIZED_FUTURE_SCOPE,
    ConsolidationPhysicalAuditor,
)
from galapagos.research.microstructure_data_contract_consolidation_readiness.validator import validate_payload  # noqa: E402

V_DISP = "V1.89"
V_NORM = "v1_89"

REQUIRED_JSON = {
    "summary": f"reports/research/microstructure_data_contract_consolidation_readiness_summary_{V_NORM}.json",
    "physical": f"reports/research/microstructure_data_contract_consolidation_readiness_physical_audit_{V_NORM}.json",
    "design": f"reports/research/microstructure_data_contract_consolidation_readiness_contract_v2_design_{V_NORM}.json",
    "approval": f"reports/research/microstructure_data_contract_consolidation_readiness_approval_decision_{V_NORM}.json",
    "safety": f"reports/research/microstructure_data_contract_consolidation_readiness_safety_check_{V_NORM}.json",
    "consistency": f"reports/research/microstructure_data_contract_consolidation_readiness_consistency_check_{V_NORM}.json",
    "latest": "reports/current/latest_metrics.json",
    "project": "reports/PROJECT_STATE.json",
    "release": f"reports/release_zip_{V_NORM}.json",
    "audit": f"reports/zip_audit_{V_NORM}.json",
    "smoke": f"reports/zip_smoke_test_{V_NORM}.json",
}


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
        if not path.with_suffix(".md").exists():
            errors.append(f"missing markdown {path.with_suffix('.md').relative_to(root)}")
    for rel in [
        "reports/REPORT_INDEX.md",
        "docs/code_review_v1_89.md",
        "docs/microstructure_data_contract_consolidation_readiness_v1_89.md",
        "reports/research/v1_89_recommendation.json",
        "reports/research/v1_89_recommendation.md",
    ]:
        if not (root / rel).exists():
            errors.append(f"missing {rel}")
    if errors:
        return errors

    for key, payload in loaded.items():
        if payload.get("version") != V_DISP:
            errors.append(f"{key}: version mismatch {payload.get('version')!r}")
    summary = loaded["summary"]
    errors.extend(f"summary: {error}" for error in validate_payload(summary))
    physical_now = ConsolidationPhysicalAuditor(root).audit()
    for field in [
        "v1_84_files_count",
        "v1_87_files_count",
        "v1_84_hashes_verified",
        "v1_87_hashes_verified",
        "v1_84_json_valid",
        "v1_87_json_valid",
        "v1_84_unexpected_files_count",
        "v1_87_unexpected_files_count",
        "forbidden_file_types_detected",
        "parquet_created",
        "csv_created",
        "sqlite_created",
        "jsonl_created",
        "db_created",
    ]:
        if summary.get(field) != physical_now.get(field):
            errors.append(f"physical data mismatch for {field}")
    if summary.get("human_approval_granted") is True:
        if summary.get("authorized_future_version") != "V1.90":
            errors.append("authorized_future_version != V1.90")
        if summary.get("authorized_future_scope") != AUTHORIZED_FUTURE_SCOPE:
            errors.append("authorized_future_scope mismatch")
    if summary.get("approval_phrase_match") is False and summary.get("human_approval_granted") is True:
        errors.append("human approval granted despite phrase mismatch")
    for source in ["latest", "project"]:
        for field in [
            "version",
            "final_verdict",
            "readiness_pack_executed",
            "consolidation_design_executed",
            "consolidation_executed",
            "approval_gate_only",
            "reports_only",
            "approval_phrase_match",
            "human_approval_granted",
            "v1_90_authorized",
            "v1_90_execution_attempted",
            "data_directory_write_attempted",
            "new_data_files_created",
            "existing_data_files_modified",
            "existing_v1_84_files_modified",
            "existing_v1_87_files_modified",
            "dataset_created",
            "network_executed",
            "trading_allowed",
            "real_orders_possible",
            "data_contract_v2_designed",
            "consolidation_plan_created",
            "future_consolidation_allowed_root",
            "future_consolidation_max_files",
            "future_consolidation_max_bytes",
            "v1_84_hashes_verified",
            "v1_87_hashes_verified",
            "release_ready_for_external_review",
            "clean_zip_ready_for_external_review",
            "smoke_test_passed",
            "blocking_reason",
        ]:
            if loaded[source].get(field) != summary.get(field):
                errors.append(f"{source}: {field} diverges from summary")
    release = loaded["release"]
    for field in ["release_ready_for_external_review", "clean_zip_ready_for_external_review"]:
        if release.get(field) is not True:
            errors.append(f"release: {field} != true")
    if release.get("blocking_reason") is not None:
        errors.append("release: blocking_reason != null")
    audit = loaded["audit"]
    if audit.get("clean_zip_ready_for_external_review") is not True:
        errors.append("audit: clean_zip_ready_for_external_review != true")
    if audit.get("forbidden_count") != 0:
        errors.append("audit: forbidden_count != 0")
    smoke = loaded["smoke"]
    if smoke.get("smoke_test_passed") is not True:
        errors.append("smoke: smoke_test_passed != true")
    if smoke.get("smoke_failed_count") != 0:
        errors.append("smoke: smoke_failed_count != 0")
    index = (root / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    if "v1_89" not in index or "V1.89" not in index:
        errors.append("REPORT_INDEX does not reference V1.89")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=V_NORM)
    args = parser.parse_args()
    if args.version != V_NORM:
        raise SystemExit(f"Unsupported version: {args.version}")
    errors = validate_report_set(PROJECT_ROOT)
    if errors:
        print("FAIL: V1.89 validation failed")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print("PASS: V1.89 consolidation readiness reports validated.")


if __name__ == "__main__":
    main()
