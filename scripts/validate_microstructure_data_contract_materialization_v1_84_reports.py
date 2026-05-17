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

from galapagos.research.microstructure_data_contract_materialization.validator import (  # noqa: E402
    validate_payload,
    validate_physical_outputs,
)

V_DISP = "V1.84"
V_NORM = "v1_84"

REQUIRED_JSON = {
    "summary": f"reports/research/microstructure_data_contract_materialization_summary_{V_NORM}.json",
    "manifest": f"reports/research/microstructure_data_contract_materialization_manifest_audit_{V_NORM}.json",
    "safety": f"reports/research/microstructure_data_contract_materialization_safety_check_{V_NORM}.json",
    "consistency": f"reports/research/microstructure_data_contract_materialization_consistency_check_{V_NORM}.json",
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
        "docs/code_review_v1_84.md",
        "docs/microstructure_data_contract_materialization_v1_84.md",
        "reports/research/v1_84_recommendation.json",
        "reports/research/v1_84_recommendation.md",
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
    errors.extend(validate_physical_outputs(root))

    for source in ["latest", "project"]:
        for field in [
            "version",
            "final_verdict",
            "approval_source_verified",
            "materialization_executed",
            "tiny_materialization_only",
            "full_dataset_created",
            "created_files_count",
            "total_data_bytes_written",
            "created_file_paths",
            "unapproved_data_write_detected",
            "parquet_created",
            "csv_created",
            "sqlite_created",
            "jsonl_created",
            "db_created",
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
    if "v1_84" not in index or "V1.84" not in index:
        errors.append("REPORT_INDEX does not reference V1.84")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=V_NORM)
    args = parser.parse_args()
    if args.version != V_NORM:
        raise SystemExit(f"Unsupported version: {args.version}")
    errors = validate_report_set(PROJECT_ROOT)
    if errors:
        print("FAIL: V1.84 validation failed")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print("PASS: V1.84 materialization reports validated.")


if __name__ == "__main__":
    main()
