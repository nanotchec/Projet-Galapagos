"""Strict validator for V1.82.2 reports."""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def validate_v1_82_2() -> bool:
    metrics_path = PROJECT_ROOT / "reports/current/latest_metrics.json"
    if not metrics_path.exists():
        print("FAIL: latest_metrics.json missing")
        return False
        
    with open(metrics_path, "r") as f:
        metrics = json.load(f)
        
    errors = []
    
    # 1. Version check
    if metrics.get("version") != "V1.82.2":
        errors.append(f"Invalid version: {metrics.get('version')}")
        
    # 2. Mandatory metrics (The 10 fields specifically requested)
    mandatory = [
        "research_dataset_updated",
        "data_contract_actual_write_executed",
        "predictions_created",
        "labels_created",
        "targets_created",
        "holdout_executed",
        "codex_cli_called",
        "pytest_executed",
        "pytest_exit_code",
        "pytest_failed_count"
    ]
    for field in mandatory:
        if field not in metrics:
            errors.append(f"Missing mandatory field: {field}")
            
    # 3. ZIP Self-Validation flags
    if not metrics.get("clean_zip_ready_for_external_review"):
        errors.append("clean_zip_ready_for_external_review is False")
        
    # 4. Safety invariants
    if not metrics.get("dry_run_only"):
        errors.append("dry_run_only is False")
    if not metrics.get("reports_only"):
        errors.append("reports_only is False")
    if metrics.get("trading_allowed"):
        errors.append("trading_allowed is True")
    if metrics.get("data_directory_write_attempted"):
        errors.append("data_directory_write_attempted is True")
        
    if errors:
        for err in errors:
            print(f"FAIL: {err}")
        return False
        
    print("PASS: V1.82.2 reports validated successfully.")
    return True

if __name__ == "__main__":
    if validate_v1_82_2():
        sys.exit(0)
    else:
        sys.exit(1)
