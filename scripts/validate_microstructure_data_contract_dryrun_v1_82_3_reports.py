"""Strict validator for V1.82.3 reports – checks all mandatory files and fields."""
import json
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def validate_v1_82_3(version: str = "v1_82_3") -> bool:
    errors = []
    
    # ── 1. Mandatory Files List ──────────────────────────────────────────
    mandatory_files = [
        f"reports/research/microstructure_data_contract_dryrun_summary_{version}.json",
        f"reports/research/microstructure_data_contract_dryrun_contract_{version}.json",
        f"reports/research/microstructure_data_contract_dryrun_safety_check_{version}.json",
        f"reports/research/microstructure_data_contract_dryrun_consistency_check_{version}.json",
        f"reports/research/v1_82_3_recommendation.json",
        f"reports/current/latest_metrics.json",
        f"reports/current/latest_summary.md",
        f"reports/PROJECT_STATE.json",
        f"reports/REPORT_INDEX.md",
        f"docs/code_review_{version}.md",
        f"docs/microstructure_data_contract_dryrun_{version}.md",
        f"reports/release_zip_{version}.json",
        f"reports/zip_audit_{version}.json",
        f"reports/zip_smoke_test_{version}.json"
    ]
    
    for rel_path in mandatory_files:
        p = PROJECT_ROOT / rel_path
        if not p.exists():
            errors.append(f"Missing mandatory file: {rel_path}")

    if errors:
        for err in errors: print(f"FAIL: {err}")
        return False

    # ── 2. release_zip_{version}.json Checks ─────────────────────────────
    with open(PROJECT_ROOT / f"reports/release_zip_{version}.json", "r") as f:
        rel_zip = json.load(f)
    if rel_zip.get("release_ready_for_external_review") != True:
        errors.append("release_ready_for_external_review is not True in release_zip")
    if rel_zip.get("clean_zip_ready_for_external_review") != True:
        errors.append("clean_zip_ready_for_external_review is not True in release_zip")
    if rel_zip.get("blocking_reason") is not None:
        errors.append(f"blocking_reason is not None in release_zip: {rel_zip.get('blocking_reason')}")

    # ── 3. zip_smoke_test_{version}.json Checks ──────────────────────────
    with open(PROJECT_ROOT / f"reports/zip_smoke_test_{version}.json", "r") as f:
        smoke = json.load(f)
    
    if smoke.get("smoke_test_passed") != True: errors.append("Zip smoke report says failed")
    if smoke.get("smoke_failed_count") != 0: errors.append("Zip smoke report has failed commands")
    if smoke.get("smoke_passed_count") != smoke.get("smoke_commands_count"):
        errors.append("Zip smoke report passed/total mismatch")
    if smoke.get("smoke_commands_not_empty") != True: errors.append("Zip smoke report commands empty")

    # ── 4. Detailed Metric Checks (from latest_metrics.json) ──────────────
    with open(PROJECT_ROOT / "reports/current/latest_metrics.json", "r") as f:
        metrics = json.load(f)

    # Version check
    if metrics.get("version") != "V1.82.3":
        errors.append(f"Invalid version: {metrics.get('version')}")

    # Safety Invariants
    safety_invariants = {
        "dry_run_only": True,
        "reports_only": True,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "dataset_created": False,
        "research_dataset_updated": False,
        "data_contract_actual_write_executed": False,
        "materialization_executed": False,
        "physical_files_created_count": 0,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "no_real_trading": True,
        "no_paper_live": True,
        "ml_signal_validation_executed": False,
        "predictions_created": False,
        "labels_created": False,
        "targets_created": False,
        "holdout_executed": False,
        "codex_cli_called": False,
    }
    for field, expected in safety_invariants.items():
        if metrics.get(field) != expected:
            errors.append(f"Safety violation: {field} is {metrics.get(field)}, expected {expected}")

    # Pytest Quality
    if metrics.get("pytest_executed") != True: errors.append("pytest_executed is not True")
    if metrics.get("pytest_exit_code") != 0: errors.append(f"pytest_exit_code is {metrics.get('pytest_exit_code')}")
    if metrics.get("pytest_failed_count") != 0: errors.append(f"pytest_failed_count is {metrics.get('pytest_failed_count')}")

    # ── 5. REPORT_INDEX.md Checks ────────────────────────────────────────
    index_content = (PROJECT_ROOT / "reports/REPORT_INDEX.md").read_text()
    if "UNFINED" in index_content: errors.append("REPORT_INDEX.md contains 'UNFINED'")
    if f"V1.82.3" not in index_content: errors.append("REPORT_INDEX.md does not reference V1.82.3")

    # ── 6. latest_summary.md Checks ──────────────────────────────────────
    summary_content = (PROJECT_ROOT / "reports/current/latest_summary.md").read_text()
    if "V1.82.3" not in summary_content: errors.append("latest_summary.md missing V1.82.3")
    for old_v in ["V1.82.2", "V1.82.1", "V1.81.16"]:
        if f"current version is {old_v}" in summary_content.lower():
            errors.append(f"latest_summary.md claims old version {old_v} as current")

    if errors:
        for err in errors: print(f"FAIL: {err}")
        return False

    print(f"PASS: {version} reports and invariants validated strictly.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1_82_3")
    args = parser.parse_args()
    if validate_v1_82_3(args.version):
        sys.exit(0)
    else:
        sys.exit(1)
