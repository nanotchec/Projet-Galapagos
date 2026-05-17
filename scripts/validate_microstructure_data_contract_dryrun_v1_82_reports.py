import argparse
import json
import os
import sys
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1_82")
    args = parser.parse_args()

    v_disp = "V1.82"
    v_norm = "v1_82"

    reports_to_check = {
        "summary": PROJECT_ROOT / f"reports/research/microstructure_data_contract_dryrun_summary_{v_norm}.json",
        "contract": PROJECT_ROOT / f"reports/research/microstructure_data_contract_dryrun_contract_{v_norm}.json",
        "safety": PROJECT_ROOT / f"reports/research/microstructure_data_contract_dryrun_safety_check_{v_norm}.json",
        "consistency": PROJECT_ROOT / f"reports/research/microstructure_data_contract_dryrun_consistency_check_{v_norm}.json",
        "metrics": PROJECT_ROOT / "reports/current/latest_metrics.json",
        "project_state": PROJECT_ROOT / "reports/PROJECT_STATE.json",
        "report_index": PROJECT_ROOT / "reports/REPORT_INDEX.md",
        "code_review": PROJECT_ROOT / f"docs/code_review_{v_norm}.md",
    }

    errors = []
    
    # Existence check
    loaded_data = {}
    for key, path in reports_to_check.items():
        if not path.exists():
            errors.append(f"Missing mandatory report: {path.name}")
        elif path.suffix == ".json":
            with open(path) as f:
                loaded_data[key] = json.load(f)

    if errors:
        print(f"ERROR: Validation {v_disp} failed (existence):\n" + "\n".join(f"  - {e}" for e in errors))
        sys.exit(1)

    # Invariant checks
    s = loaded_data["summary"]
    m = loaded_data["metrics"]
    ps = loaded_data["project_state"]

    for d_name, d in [("summary", s), ("metrics", m), ("project_state", ps)]:
        if d.get("version") != v_disp: errors.append(f"{d_name}: version mismatch")
        if d.get("dry_run_only") is not True: errors.append(f"{d_name}: dry_run_only != True")
        if d.get("reports_only") is not True: errors.append(f"{d_name}: reports_only != True")
        if d.get("network_executed") is not False: errors.append(f"{d_name}: network_executed != False")
        if d.get("data_directory_writes_allowed") is not False: errors.append(f"{d_name}: data_directory_writes_allowed != False")
        if d.get("data_directory_write_attempted") is not False: errors.append(f"{d_name}: data_directory_write_attempted != False")
        if d.get("new_data_files_created") is not False: errors.append(f"{d_name}: new_data_files_created != False")
        if d.get("no_data_directory_writes") is not True: errors.append(f"{d_name}: no_data_directory_writes != True")
        if d.get("parquet_created") is not False: errors.append(f"{d_name}: parquet_created != False")
        if d.get("csv_created") is not False: errors.append(f"{d_name}: csv_created != False")
        if d.get("sqlite_created") is not False: errors.append(f"{d_name}: sqlite_created != False")
        if d.get("jsonl_created") is not False: errors.append(f"{d_name}: jsonl_created != False")
        if d.get("db_created") is not False: errors.append(f"{d_name}: db_created != False")
        if d.get("dataset_created") is not False: errors.append(f"{d_name}: dataset_created != False")
        if d.get("materialization_executed") is not False: errors.append(f"{d_name}: materialization_executed != False")
        if d.get("data_contract_actual_write_executed") is not False: errors.append(f"{d_name}: data_contract_actual_write_executed != False")
        if d.get("theoretical_paths_only") is not True: errors.append(f"{d_name}: theoretical_paths_only != True")
        if d.get("theoretical_schema_only") is not True: errors.append(f"{d_name}: theoretical_schema_only != True")
        if d.get("theoretical_manifest_only") is not True: errors.append(f"{d_name}: theoretical_manifest_only != True")
        if d.get("physical_files_created_count") != 0: errors.append(f"{d_name}: physical_files_created_count != 0")
        if d.get("dryrun_preview_records_count", 0) > 5: errors.append(f"{d_name}: dryrun_preview_records_count > 5")
        if d.get("future_write_requires_new_human_approval") is not True: errors.append(f"{d_name}: future_write_requires_new_human_approval != True")
        if d.get("trading_allowed") is not False: errors.append(f"{d_name}: trading_allowed != False")
        if d.get("real_orders_possible") is not False: errors.append(f"{d_name}: real_orders_possible != False")
        if d.get("no_real_trading") is not True: errors.append(f"{d_name}: no_real_trading != True")
        if d.get("ml_signal_validation_executed") is not False: errors.append(f"{d_name}: ml_signal_validation_executed != False")

    # Release and Index
    if v_disp not in reports_to_check["report_index"].read_text():
        errors.append("REPORT_INDEX.md does not reference V1.82")

    if errors:
        print(f"ERROR: Validation {v_disp} failed ({len(errors)}):\n" + "\n".join(f"  - {e}" for e in errors))
        sys.exit(1)

    print(f"SUCCESS: {v_disp} VALIDATED (Cross-file alignment OK).")

if __name__ == "__main__":
    main()
