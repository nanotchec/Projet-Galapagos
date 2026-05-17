from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

def validate_reports(version: str):
    v_norm = version.lower().replace(".", "_")
    report_dir = Path("reports/research")
    
    summary_path = report_dir / f"recent_regime_diagnostic_summary_{v_norm}.json"
    rebuild_path = report_dir / f"recent_regime_selected_filter_rebuild_{v_norm}.json"
    
    if not summary_path.exists() or not rebuild_path.exists():
        print("FAIL: Missing core reports")
        return False
        
    with open(summary_path) as f:
        summary = json.load(f)
    with open(rebuild_path) as f:
        rebuild = json.load(f)
        
    errors = []
    
    # 1. Trade unit consistency
    selected_count = summary.get("selected_count_final")
    if selected_count != 225:
        errors.append(f"Selected count mismatch: expected 225, got {selected_count}")
    
    if selected_count == 5594:
        errors.append("Selected count still uses raw rows (5594 detected)")
        
    # 2. Leakage check
    forbidden_found = rebuild.get("forbidden_columns_found", [])
    if forbidden_found:
        errors.append(f"Selection leakage detected: {forbidden_found}")
        
    if rebuild.get("filters_received_outcomes") != False:
        errors.append("Filters reported receiving outcome columns")
        
    if rebuild.get("rebuild_status") != "REBUILD_COMPLETE_NO_SELECTION_LEAKAGE":
        errors.append(f"Rebuild status invalid: {rebuild.get('rebuild_status')}")

    # 3. Prudent verdicts
    regime_status = summary.get("regime_dependency_status")
    regime_def = summary.get("regime_definition_status")
    if regime_def == "REGIME_DEFINITION_TOO_COARSE" and regime_status == "BULL_REGIME_DEPENDENT":
        errors.append("Regime status too affirmative for coarse definition")
        
    cost_status = summary.get("cost_drag_status")
    # Load cost report to check measurable
    cost_path = report_dir / f"cost_drag_diagnostic_{v_norm}.json"
    if cost_path.exists():
        with open(cost_path) as f:
            cost_data = json.load(f)
            if not cost_data.get("cost_drag_measurable") and "NOT_ISOLATED" not in cost_status:
                errors.append("Cost drag status too affirmative for non-measurable costs")
                
    # 3. Standard naming
    required_reports = [
        f"recent_window_diagnostic_{v_norm}.json",
        f"regime_dependency_diagnostic_{v_norm}.json",
        f"calibration_drift_diagnostic_{v_norm}.json",
        f"cost_drag_diagnostic_{v_norm}.json",
        f"outcome_distribution_diagnostic_{v_norm}.json",
        f"regime_definition_audit_{v_norm}.json"
    ]
    for r in required_reports:
        if not (report_dir / r).exists():
            errors.append(f"Missing required report: {r}")
            
    # 4. Mandatory block
    if summary.get("do_not_progress_to_v1_30") != True:
        errors.append("V1.30 block missing in summary")
        
    consistency_status = "RECENT_REGIME_DIAGNOSTIC_CONSISTENT_NO_SELECTION_LEAKAGE" if not errors else "CONSISTENCY_FAILED"
    
    res = {
        "version": version,
        "consistency_status": consistency_status,
        "errors": errors,
        "selected_count_final": selected_count,
        "selected_count_matches_v1_29_3": selected_count == 225
    }
    
    output_path_json = report_dir / f"recent_regime_diagnostic_consistency_check_{v_norm}.json"
    with open(output_path_json, "w") as f:
        json.dump(res, f, indent=2)
        
    output_path_md = report_dir / f"recent_regime_diagnostic_consistency_check_{v_norm}.md"
    with open(output_path_md, "w") as f:
        f.write(f"# Consistency Check - {version}\n\n")
        f.write(f"- Status: {consistency_status}\n")
        f.write(f"- Selected Count: {selected_count}\n")
        f.write(f"- Matches V1.29.3: {selected_count == 225}\n\n")
        if errors:
            f.write("## Errors\n")
            for e in errors:
                f.write(f"- {e}\n")
        
    print(f"Consistency check: {consistency_status}")
    for e in errors:
        print(f"  - ERROR: {e}")
        
    return not errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    
    success = validate_reports(args.version)
    if not success:
        sys.exit(1)
