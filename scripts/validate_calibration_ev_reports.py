from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

# Add src to path
sys.path.append(os.path.abspath("src"))

def validate_reports(version: str, report_dir: str = "reports/research") -> dict[str, Any]:
    v_suffix = version.replace(".", "_")
    
    expected_reports = [
        "point_in_time_feature_audit",
        "prediction_frame_integrity",
        "calibration_global",
        "reliability_bins",
        "calibration_temporal",
        "calibration_regime",
        "payoff_asymmetry",
        "cost_model_foundation",
        "expected_value_proxy",
        "calibration_ev_summary",
        "recommendation"
    ]
    
    missing = []
    found_reports = {}
    
    for report_key in expected_reports:
        if report_key == "recommendation":
            filename = f"{v_suffix}_{report_key}.json"
        else:
            filename = f"{report_key}_{v_suffix}.json"
            
        path = os.path.join(report_dir, filename)
        if not os.path.exists(path):
            missing.append(filename)
        else:
            with open(path) as f:
                found_reports[report_key] = json.load(f)
                
    if missing:
        return {
            "version": version,
            "status": "CALIBRATION_EV_REPORTS_INCOMPLETE",
            "missing_reports": missing,
            "issues": [f"Missing reports: {', '.join(missing)}"]
        }
        
    # Consistency checks
    issues = []
    summary = found_reports.get("calibration_ev_summary", {})
    global_cal = found_reports.get("calibration_global", {})
    recs = found_reports.get("recommendation", {})
    integrity = found_reports.get("prediction_frame_integrity", {})
    pit = found_reports.get("point_in_time_feature_audit", {})
    cost = found_reports.get("cost_model_foundation", {})
    
    # 1. Fail if any central status contains FAILED
    central_statuses = {
        "point_in_time_status": pit.get("point_in_time_status"),
        "prediction_frame_integrity_status": integrity.get("integrity_status"),
        "calibration_global_status": summary.get("calibration_global_status"),
        "cost_model_status": cost.get("cost_model_status"),
        "ev_proxy_status": summary.get("ev_proxy_status")
    }
    for label, stat in central_statuses.items():
        if not stat:
            issues.append(f"{label} missing")
        elif "FAILED" in stat:
            issues.append(f"{label} FAILED: {stat}")
            
    # 2. Strict Leakage checks
    if integrity.get("integrity_status") != "PREDICTION_FRAME_INTEGRITY_PASSED":
        issues.append("PREDICTION_FRAME_INTEGRITY_STATUS_NOT_PASSED")
    if integrity.get("forbidden_columns_in_selection") != []:
        issues.append("FORBIDDEN_COLUMNS_FOUND_IN_SELECTION")
    if integrity.get("filters_received_outcomes") is not False:
        issues.append("FILTERS_RECEIVED_OUTCOMES_NOT_FALSE")
        
    # 3. Metrics check
    if "brier_score" not in global_cal or global_cal.get("brier_score") is None:
        issues.append("brier_score missing or null")
    if "ece" not in global_cal or global_cal.get("ece") is None:
        issues.append("ece missing or null")
        
    # 4. Safety constraints
    safety_checks = {
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True
    }
    for key, val in safety_checks.items():
        if recs.get(key) != val:
            issues.append(f"Safety check failed: {key} is {recs.get(key)}, expected {val}")
            
    status = "CALIBRATION_EV_REPORTS_CONSISTENT_NO_SELECTION_LEAKAGE"
    if issues:
        status = "CALIBRATION_EV_REPORTS_INCONSISTENT"
        
    return {
        "version": version,
        "status": status,
        "issues": issues,
        "point_in_time_status": pit.get("point_in_time_status"),
        "prediction_frame_integrity_status": integrity.get("integrity_status"),
        "calibration_global_status": summary.get("calibration_global_status"),
        "brier_score": global_cal.get("brier_score"),
        "ece": global_cal.get("ece"),
        "cost_model_status": cost.get("cost_model_status"),
        "ev_proxy_status": summary.get("ev_proxy_status"),
        "final_verdict": summary.get("final_verdict"),
        "raw_dataset_contains_outcomes": pit.get("raw_dataset_contains_outcomes"),
        "raw_dataset_outcomes_classified": pit.get("raw_dataset_outcomes_classified"),
        "costs_isolated_from_gross": cost.get("costs_isolated_from_gross")
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    
    res = validate_reports(args.version)
    
    output_dir = "reports/research"
    v_suffix = args.version.replace(".", "_")
    base_name = f"calibration_ev_consistency_check_{v_suffix}"
    
    # Write JSON
    with open(os.path.join(output_dir, f"{base_name}.json"), "w") as f:
        json.dump(res, f, indent=2)
        
    # Write MD
    with open(os.path.join(output_dir, f"{base_name}.md"), "w") as f:
        f.write(f"# Calibration EV Consistency Check - {args.version}\n\n")
        f.write(f"Status: **{res['status']}**\n\n")
        if res["issues"]:
            f.write("## Issues\n")
            for issue in res["issues"]:
                f.write(f"- {issue}\n")
        f.write("\n## Details\n")
        f.write("```json\n")
        f.write(json.dumps(res, indent=2))
        f.write("\n```\n")
        
    print(f"Validation complete: {res['status']}")
    if res["status"] not in ["CALIBRATION_EV_REPORTS_CONSISTENT", "CALIBRATION_EV_REPORTS_CONSISTENT_NO_SELECTION_LEAKAGE"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
