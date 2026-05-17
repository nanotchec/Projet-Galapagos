from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V_DISP = "V1.81.16"
V_NORM = "v1_81_16"
FINAL_VERDICT = "V1_81_16_EMBEDDED_RELEASE_AND_SMOKE_CONSISTENCY_PASSED"


def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=V_NORM)
    args = parser.parse_args()
    if args.version != V_NORM:
        raise SystemExit(f"Unsupported version: {args.version}")

    paths = {
        "summary": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_summary_{V_NORM}.json",
        "pytest": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_pytest_audit_{V_NORM}.json",
        "negative": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_negative_coverage_{V_NORM}.json",
        "quality": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_test_quality_audit_{V_NORM}.json",
        "anti": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_anti_tautology_audit_{V_NORM}.json",
        "current": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_current_state_alignment_{V_NORM}.json",
        "consistency": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_consistency_check_{V_NORM}.json",
        "latest": PROJECT_ROOT / "reports/current/latest_metrics.json",
        "project": PROJECT_ROOT / "reports/PROJECT_STATE.json",
        "audit": PROJECT_ROOT / f"reports/zip_audit_{V_NORM}.json",
        "smoke": PROJECT_ROOT / f"reports/zip_smoke_test_{V_NORM}.json",
        "release": PROJECT_ROOT / f"reports/release_zip_{V_NORM}.json",
    }
    docs = [
        PROJECT_ROOT / "reports/REPORT_INDEX.md",
        PROJECT_ROOT / f"docs/code_review_{V_NORM}.md",
    ]
    errors: list[str] = []
    for path in list(paths.values()) + docs:
        if not path.exists():
            errors.append(f"missing {path}")
        if path.suffix == ".json":
            md_path = path.with_suffix(".md")
            if not md_path.exists():
                errors.append(f"missing markdown {md_path}")
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)

    data = {key: _load(path) for key, path in paths.items()}
    for key, payload in data.items():
        if not _finite(payload):
            errors.append(f"{key}: JSON contains NaN/Infinity")
        if payload.get("version") != V_DISP:
            errors.append(f"{key}: version mismatch {payload.get('version')}")

    summary = data["summary"]
    release = data["release"]
    quality = data["quality"]
    smoke = data["smoke"]
    audit = data["audit"]

    release_required = {
        "release_zip_created": True,
        "final_zip_created": True,
        "release_ready_for_external_review": True,
        "final_audit_passed": True,
        "final_smoke_passed": True,
        "clean_zip_ready_for_external_review": True,
        "required_reports_present": True,
        "required_docs_present": True,
        "report_index_updated": True,
    }
    for field, expected in release_required.items():
        if release.get(field) is not expected:
            errors.append(f"release_zip: {field} != {expected}")
    if release.get("blocking_reason") is not None:
        errors.append("release_zip: blocking_reason is not null")

    for field in ["release_ready_for_external_review", "final_audit_passed", "final_smoke_passed", "clean_zip_ready_for_external_review"]:
        values = {key: data[key].get(field) for key in ["summary", "latest", "project", "release"]}
        if set(values.values()) != {True}:
            errors.append(f"{field} diverges: {values}")
    blocking = {key: data[key].get("blocking_reason") for key in ["summary", "latest", "project", "release"]}
    if set(blocking.values()) != {None}:
        errors.append(f"blocking_reason diverges: {blocking}")

    quality_required = {
        "test_quality_passed": True,
        "quality_audit_results_forced": False,
        "forbidden_test_names_count": 0,
        "weak_tests_count": 0,
        "tautological_tests_count": 0,
        "or_true_tests_count": 0,
        "assert_true_tests_count": 0,
    }
    for field, expected in quality_required.items():
        if quality.get(field) != expected:
            errors.append(f"quality: {field} != {expected}")
        if summary.get(field) != expected:
            errors.append(f"summary: {field} != {expected}")

    if smoke.get("smoke_test_passed") is not True:
        errors.append("smoke: smoke_test_passed != true")
    if smoke.get("smoke_failed_count") != 0:
        errors.append("smoke: smoke_failed_count != 0")
    if smoke.get("smoke_passed_count") != smoke.get("smoke_commands_count"):
        errors.append("smoke: passed count mismatch")
    if audit.get("clean_zip_ready_for_external_review") is not True:
        errors.append("audit: clean_zip_ready_for_external_review != true")

    safety_checks = {
        "network_executed": False,
        "new_network_requests_executed": False,
        "data_directory_writes_allowed": False,
        "dataset_created": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "no_real_trading": True,
        "no_paper_live": True,
        "v1_82_execution_attempted": False,
        "data_contract_dryrun_executed": False,
    }
    for key in ["summary", "latest", "project"]:
        for field, expected in safety_checks.items():
            if data[key].get(field) is not expected:
                errors.append(f"{key}: {field} != {expected}")

    if summary.get("final_verdict") != FINAL_VERDICT:
        errors.append("summary final verdict mismatch")
    report_index = (PROJECT_ROOT / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    if "v1_81_16" not in report_index:
        errors.append("REPORT_INDEX does not reference v1_81_16")
    test_text = (PROJECT_ROOT / f"tests/research/test_microstructure_data_contract_approval_intake_{V_NORM}.py").read_text(encoding="utf-8")
    if "parametrize(\"i\", range(" in test_text or "parametrize('i', range(" in test_text:
        errors.append("test file contains artificial parametrize range padding")

    if errors:
        print("ERROR: V1.81.16 validation failed:")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print("SUCCESS: V1.81.16 reports validated.")


if __name__ == "__main__":
    main()
