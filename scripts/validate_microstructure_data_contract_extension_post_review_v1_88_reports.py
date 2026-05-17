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

from galapagos.research.microstructure_data_contract_extension_post_review.reviewer import (  # noqa: E402
    ExtensionPostReviewReviewer,
)
from galapagos.research.microstructure_data_contract_extension_post_review.validator import validate_payload  # noqa: E402

V_DISP = "V1.88"
V_NORM = "v1_88"

REQUIRED_JSON = {
    "summary": f"reports/research/microstructure_data_contract_extension_post_review_summary_{V_NORM}.json",
    "physical": f"reports/research/microstructure_data_contract_extension_post_review_physical_audit_{V_NORM}.json",
    "safety": f"reports/research/microstructure_data_contract_extension_post_review_safety_check_{V_NORM}.json",
    "consistency": f"reports/research/microstructure_data_contract_extension_post_review_consistency_check_{V_NORM}.json",
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
        "docs/code_review_v1_88.md",
        "docs/microstructure_data_contract_extension_post_review_v1_88.md",
        "reports/research/v1_88_recommendation.json",
        "reports/research/v1_88_recommendation.md",
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
    physical_now = ExtensionPostReviewReviewer(root).review()
    for field in [
        "reviewed_v1_84_files_count",
        "reviewed_v1_87_files_count",
        "unexpected_v1_84_files_count",
        "unexpected_v1_87_files_count",
        "missing_v1_84_files_count",
        "missing_v1_87_files_count",
        "total_v1_87_data_bytes_observed",
        "v1_87_extension_manifest_json_valid",
        "v1_87_extension_quality_summary_json_valid",
        "v1_87_manifest_matches_physical_files",
        "v1_84_hashes_match_expected",
        "v1_87_hashes_match_expected",
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
            "post_extension_review_executed",
            "review_only",
            "reports_only",
            "extension_materialization_executed",
            "new_extension_materialization_executed",
            "materialization_executed",
            "data_contract_actual_write_executed",
            "data_directory_write_attempted",
            "new_data_files_created",
            "existing_data_files_modified",
            "existing_v1_84_files_modified",
            "existing_v1_87_files_modified",
            "reviewed_v1_84_files_count",
            "reviewed_v1_87_files_count",
            "unexpected_v1_87_files_count",
            "missing_v1_87_files_count",
            "total_v1_87_data_bytes_observed",
            "v1_87_manifest_matches_physical_files",
            "v1_84_hashes_match_expected",
            "v1_87_hashes_match_expected",
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
    if "v1_88" not in index or "V1.88" not in index:
        errors.append("REPORT_INDEX does not reference V1.88")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=V_NORM)
    args = parser.parse_args()
    if args.version != V_NORM:
        raise SystemExit(f"Unsupported version: {args.version}")
    errors = validate_report_set(PROJECT_ROOT)
    if errors:
        print("FAIL: V1.88 validation failed")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print("PASS: V1.88 post-extension review reports validated.")


if __name__ == "__main__":
    main()
