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

from galapagos.research.microstructure_data_contract_extension_gate.validator import validate_payload  # noqa: E402

V_DISP = "V1.86"
V_NORM = "v1_86"

REQUIRED_JSON = {
    "summary": f"reports/research/microstructure_data_contract_extension_gate_summary_{V_NORM}.json",
    "decision": f"reports/research/microstructure_data_contract_extension_gate_decision_{V_NORM}.json",
    "safety": f"reports/research/microstructure_data_contract_extension_gate_safety_check_{V_NORM}.json",
    "consistency": f"reports/research/microstructure_data_contract_extension_gate_consistency_check_{V_NORM}.json",
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
        "docs/code_review_v1_86.md",
        "docs/microstructure_data_contract_extension_gate_v1_86.md",
        "reports/research/v1_86_recommendation.json",
        "reports/research/v1_86_recommendation.md",
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
    for source in ["latest", "project"]:
        for field in [
            "version",
            "final_verdict",
            "approval_phrase_match",
            "human_approval_granted",
            "v1_87_authorized",
            "authorized_future_scope",
            "v1_87_execution_attempted",
            "materialization_executed",
            "new_materialization_executed",
            "data_contract_actual_write_executed",
            "data_directory_write_attempted",
            "new_data_files_created",
            "existing_data_files_modified",
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
    if "v1_86" not in index or "V1.86" not in index:
        errors.append("REPORT_INDEX does not reference V1.86")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=V_NORM)
    args = parser.parse_args()
    if args.version != V_NORM:
        raise SystemExit(f"Unsupported version: {args.version}")
    errors = validate_report_set(PROJECT_ROOT)
    if errors:
        print("FAIL: V1.86 validation failed")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print("PASS: V1.86 extension approval gate reports validated.")


if __name__ == "__main__":
    main()
