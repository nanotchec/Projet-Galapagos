"""Strict Cross-File Validator for V1.82.4 reports."""
import json
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CRITICAL_CROSS_FILE_FIELDS = [
    "version",
    "final_verdict",
    "dry_run_only",
    "reports_only",
    "network_executed",
    "new_network_requests_executed",
    "data_directory_writes_allowed",
    "data_directory_write_attempted",
    "new_data_files_created",
    "no_data_directory_writes",
    "parquet_created",
    "csv_created",
    "sqlite_created",
    "jsonl_created",
    "db_created",
    "dataset_created",
    "research_dataset_updated",
    "data_contract_actual_write_executed",
    "materialization_executed",
    "physical_files_created_count",
    "trading_allowed",
    "real_orders_possible",
    "no_real_trading",
    "no_paper_live",
    "ml_signal_validation_executed",
    "predictions_created",
    "labels_created",
    "targets_created",
    "holdout_executed",
    "codex_cli_called",
    "pytest_executed",
    "pytest_exit_code",
    "pytest_failed_count",
    "release_ready_for_external_review",
    "clean_zip_ready_for_external_review",
    "smoke_test_passed",
    "blocking_reason"
]

def validate_v1_82_4(version: str = "v1_82_4") -> bool:
    errors = []
    
    # ── 1. Mandatory Files ──────────────────────────────────────────────
    mandatory_files = [
        f"reports/research/microstructure_data_contract_dryrun_summary_{version}.json",
        f"reports/research/microstructure_data_contract_dryrun_contract_{version}.json",
        f"reports/research/microstructure_data_contract_dryrun_safety_check_{version}.json",
        f"reports/research/microstructure_data_contract_dryrun_consistency_check_{version}.json",
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
        if not (PROJECT_ROOT / rel_path).exists():
            errors.append(f"Missing mandatory file: {rel_path}")

    if errors:
        for err in errors: print(f"FAIL: {err}")
        return False

    # ── 2. Load Core JSONs ──────────────────────────────────────────────
    try:
        with open(PROJECT_ROOT / f"reports/research/microstructure_data_contract_dryrun_summary_{version}.json", "r") as f:
            summary = json.load(f)
        with open(PROJECT_ROOT / "reports/current/latest_metrics.json", "r") as f:
            metrics = json.load(f)
        with open(PROJECT_ROOT / "reports/PROJECT_STATE.json", "r") as f:
            state = json.load(f)
    except Exception as e:
        print(f"FAIL: Error loading JSON files: {e}")
        return False

    # ── 3. Cross-File Field Comparison ──────────────────────────────────
    for field in CRITICAL_CROSS_FILE_FIELDS:
        # We use a unique object for missing values to distinguish from None
        MISSING = object()
        vals = {
            "summary": summary.get(field, MISSING),
            "latest_metrics": metrics.get(field, MISSING),
            "PROJECT_STATE": state.get(field, MISSING)
        }
        
        # Check for missing fields
        for source, val in vals.items():
            if val is MISSING:
                errors.append(f"Field '{field}' is MISSING in {source}")
        
        # Check for mismatches (only if not missing)
        actual_vals = [v for v in vals.values() if v is not MISSING]
        if len(set(str(v) for v in actual_vals)) > 1:
            errors.append(f"Mismatch for field '{field}': summary={vals['summary']}, metrics={vals['latest_metrics']}, state={vals['PROJECT_STATE']}")

    # ── 4. Strict Safety Invariants (on metrics, which should match others) ──
    invariants = {
        "dry_run_only": True,
        "reports_only": True,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
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
        "pytest_executed": True,
        "pytest_exit_code": 0,
        "pytest_failed_count": 0,
    }
    for field, expected in invariants.items():
        if metrics.get(field) != expected:
            errors.append(f"Safety violation: {field} is {metrics.get(field)}, expected {expected}")

    # ── 5. Doc & Index Checks ───────────────────────────────────────────
    summary_md = (PROJECT_ROOT / "reports/current/latest_summary.md").read_text()
    if "V1.82.4" not in summary_md: errors.append("latest_summary.md missing V1.82.4")
    for old_v in ["V1.82.3", "V1.82.2", "V1.82.1", "V1.81.16"]:
        if f"current version is {old_v}" in summary_md.lower():
            errors.append(f"latest_summary.md claims old version {old_v} as current")

    index_content = (PROJECT_ROOT / "reports/REPORT_INDEX.md").read_text()
    if "UNFINED" in index_content: errors.append("REPORT_INDEX.md contains 'UNFINED'")
    if "V1.82.4" not in index_content: errors.append("REPORT_INDEX.md missing V1.82.4")

    # ── 6. Smoke Test Specifics ─────────────────────────────────────────
    with open(PROJECT_ROOT / f"reports/zip_smoke_test_{version}.json", "r") as f:
        smoke = json.load(f)
    if smoke.get("smoke_test_passed") != True: errors.append("Zip smoke report says failed")
    # Be more robust with smoke_failed_count check
    failed_count = smoke.get("smoke_failed_count")
    if failed_count is not None and failed_count != 0:
        errors.append(f"Zip smoke report has failed commands: {failed_count}")
    elif failed_count is None:
        errors.append("Zip smoke report missing smoke_failed_count")

    if errors:
        for err in errors: print(f"FAIL: {err}")
        return False

    print(f"PASS: {version} strict cross-file validation successful.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1_82_4")
    args = parser.parse_args()
    if validate_v1_82_4(args.version):
        sys.exit(0)
    else:
        sys.exit(1)
