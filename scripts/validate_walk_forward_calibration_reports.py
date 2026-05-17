from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def validate_reports(version: str, report_dir: str = "reports/research") -> dict[str, Any]:
    """
    Validate V1.31.1 walk-forward calibration reports for consistency and placeholders.
    """
    v_suffix = version.replace(".", "_")
    
    required_keys = [
        "walk_forward_calibration_splits",
        "walk_forward_calibration_leakage_audit",
        "walk_forward_calibration_comparison",
        "walk_forward_calibration_temporal",
        "walk_forward_reliability_bins",
        "walk_forward_calibration_summary",
        "ev_after_calibration_diagnostic",
        "recommendation"
    ]
    
    issues = []
    
    # 1. Check file existence
    loaded_reports = {}
    for key in required_keys:
        base_name = f"{v_suffix}_{key}" if key == "recommendation" else f"{key}_{v_suffix}"
        path = Path(report_dir) / f"{base_name}.json"
        
        if not path.exists():
            issues.append(f"Missing required report: {path}")
            continue
            
        with open(path) as f:
            loaded_reports[key] = json.load(f)

    if len(loaded_reports) < len(required_keys):
        return {"status": "WALK_FORWARD_CALIBRATION_REPORTS_INCOMPLETE", "issues": issues}

    # 2. Check Summary fields
    summary = loaded_reports["walk_forward_calibration_summary"]
    required_summary_fields = [
        "best_method_by_ece", "best_method_by_brier", 
        "calibration_stable_2026", "2026_raw_ece", "2026_calibrated_ece"
    ]
    for field in required_summary_fields:
        if field not in summary:
            issues.append(f"Summary missing required field: {field}")
            
    # 3. Check stability is calculated
    if summary.get("calibration_stable_2026") is None:
        issues.append("calibration_stable_2026 is missing or null")

    # 4. Check PROJECT_STATE consistency
    ps_path = Path("reports/PROJECT_STATE.json")
    if ps_path.exists():
        with open(ps_path) as f:
            ps = json.load(f)
            
        if ps.get("version", "").upper() != version.upper():
            issues.append(f"PROJECT_STATE version mismatch: {ps.get('version')} vs {version}")
            
        # Check cross-consistency
        if ps.get("best_method_by_ece") != summary.get("best_method_by_ece"):
            issues.append(f"PROJECT_STATE best_method_by_ece mismatch with summary: {ps.get('best_method_by_ece')} vs {summary.get('best_method_by_ece')}")
            
        if ps.get("calibration_stable_2026") != summary.get("calibration_stable_2026"):
            issues.append("PROJECT_STATE calibration_stable_2026 mismatch with summary")

    # 5. Scan for placeholders in code
    forbidden_strings = ["# Placeholder", "placeholder", "TODO", "calibration_stable_2026\": True", "calibration_stable_2026 = True"]
    files_to_scan = [
        "scripts/run_walk_forward_calibration.py",
        "src/galapagos/research/walk_forward_calibration/recommendation_engine.py",
        "src/galapagos/research/walk_forward_calibration/calibration_runner.py"
    ]
    
    for f_path in files_to_scan:
        if os.path.exists(f_path):
            with open(f_path) as f:
                content = f.read()
                for s in forbidden_strings:
                    if s in content:
                        issues.append(f"Forbidden string '{s}' found in {f_path}")

    # 6. Check safety constraints
    recs = loaded_reports["recommendation"]
    safety_checks = {
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "holdout_executed": False,
        "no_real_trading": True
    }
    for k, v in safety_checks.items():
        if recs.get(k) != v:
            issues.append(f"Safety constraint violation: {k} is {recs.get(k)}, expected {v}")

    status = "WALK_FORWARD_CALIBRATION_REPORTS_CONSISTENT_NO_PLACEHOLDERS" if not issues else "WALK_FORWARD_CALIBRATION_REPORTS_INCONSISTENT"
    
    return {
        "status": status,
        "issues": issues,
        "report_count": len(loaded_reports),
        "version": version
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--report-dir", default="reports/research")
    args = parser.parse_args()
    
    res = validate_reports(args.version, args.report_dir)
    
    v_suffix = args.version.replace(".", "_")
    output_path = Path(args.report_dir) / f"walk_forward_calibration_consistency_check_{v_suffix}.json"
    
    with open(output_path, "w") as f:
        json.dump(res, f, indent=2)
        
    # Write MD report
    md_path = output_path.with_suffix(".md")
    with open(md_path, "w") as f:
        f.write(f"# Walk-Forward Calibration Consistency Check - {args.version}\n\n")
        f.write(f"Status: **{res['status']}**\n\n")
        if res["issues"]:
            f.write("## Issues Found\n")
            for issue in res["issues"]:
                f.write(f"- {issue}\n")
        else:
            f.write("No issues detected.\n")
            
        f.write("\n## Details\n")
        f.write("```json\n")
        f.write(json.dumps(res, indent=2))
        f.write("\n```\n")
        
    print(f"Validation complete: {res['status']}")
    if res["status"] != "WALK_FORWARD_CALIBRATION_REPORTS_CONSISTENT_NO_PLACEHOLDERS":
        sys.exit(1)


if __name__ == "__main__":
    main()
