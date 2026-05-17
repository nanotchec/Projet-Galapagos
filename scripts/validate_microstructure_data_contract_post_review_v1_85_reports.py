from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from galapagos.research.microstructure_data_contract_post_review.reviewer import (  # noqa: E402
    PostMaterializationReviewer,
)
from galapagos.research.microstructure_data_contract_post_review.validator import validate_payload  # noqa: E402

V_DISP = "V1.85"
V_NORM = "v1_85"

REQUIRED_JSON = {
    "summary": f"reports/research/microstructure_data_contract_post_review_summary_{V_NORM}.json",
    "physical": f"reports/research/microstructure_data_contract_post_review_physical_audit_{V_NORM}.json",
    "safety": f"reports/research/microstructure_data_contract_post_review_safety_check_{V_NORM}.json",
    "consistency": f"reports/research/microstructure_data_contract_post_review_consistency_check_{V_NORM}.json",
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
        "docs/code_review_v1_85.md",
        "docs/microstructure_data_contract_post_review_v1_85.md",
        "reports/research/v1_85_recommendation.json",
        "reports/research/v1_85_recommendation.md",
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
    dryrun_contract = _load(root / "reports/research/microstructure_data_contract_dryrun_contract_v1_82_4.json")
    physical_now = PostMaterializationReviewer(root).review(dryrun_contract=dryrun_contract)
    for field in [
        "reviewed_files_count",
        "unexpected_files_count",
        "missing_expected_files_count",
        "total_data_bytes_observed",
        "preview_records_count",
        "manifest_json_valid",
        "schema_snapshot_json_valid",
        "preview_records_json_valid",
        "manifest_matches_physical_files",
        "schema_snapshot_matches_contract",
        "parquet_created",
        "csv_created",
        "sqlite_created",
        "jsonl_created",
        "db_created",
    ]:
        if summary.get(field) != physical_now.get(field):
            errors.append(f"physical data mismatch for {field}")
    for source in ["latest", "project"]:
        for field in [
            "version",
            "final_verdict",
            "post_materialization_review_executed",
            "review_only",
            "reports_only",
            "materialization_executed",
            "new_materialization_executed",
            "data_contract_actual_write_executed",
            "data_directory_write_attempted",
            "new_data_files_created",
            "existing_data_files_modified",
            "reviewed_files_count",
            "unexpected_files_count",
            "missing_expected_files_count",
            "total_data_bytes_observed",
            "preview_records_count",
            "manifest_matches_physical_files",
            "schema_snapshot_matches_contract",
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
    if "v1_85" not in index or "V1.85" not in index:
        errors.append("REPORT_INDEX does not reference V1.85")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=V_NORM)
    args = parser.parse_args()
    if args.version != V_NORM:
        raise SystemExit(f"Unsupported version: {args.version}")
    errors = validate_report_set(PROJECT_ROOT)
    if errors:
        print("FAIL: V1.85 validation failed")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print("PASS: V1.85 post-materialization review reports validated.")


if __name__ == "__main__":
    main()
