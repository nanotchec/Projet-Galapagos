"""Validator for Microstructure Quality Mask reports (V1.51.1)."""
import argparse
import json
import math
from pathlib import Path

def check_finite(obj):
    if isinstance(obj, dict):
        return all(check_finite(v) for v in obj.values())
    elif isinstance(obj, list):
        return all(check_finite(x) for x in obj)
    elif isinstance(obj, float):
        return math.isfinite(obj)
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.51.1")
    args = parser.parse_args()
    
    version = args.version.upper()
    v_norm = version.lower().replace(".", "_")
    report_dir = Path("reports/research")
    
    mandatory_reports = [
        "microstructure_quality_mask_input_guard",
        "microstructure_quality_rule_set",
        "microstructure_coverage_mask",
        "microstructure_mask_impact_analysis",
        "microstructure_usable_window_analysis",
        "microstructure_blocked_window_analysis",
        "microstructure_feature_retention_analysis",
        "microstructure_label_reliability_under_mask",
        "microstructure_data_action_plan",
        "microstructure_quality_mask_scorecard",
        "microstructure_quality_mask_recommendation",
        "microstructure_quality_mask_summary",
        "microstructure_quality_mask_consistency_check",
        f"{v_norm}_recommendation"
    ]
    
    print(f"Validating {version} reports...")
    
    for r in mandatory_reports:
        if r == f"{v_norm}_recommendation":
             json_path = report_dir / f"{r}.json"
             md_path = report_dir / f"{r}.md"
        else:
             json_path = report_dir / f"{r}_{v_norm}.json"
             md_path = report_dir / f"{r}_{v_norm}.md"
        
        if not json_path.exists():
            print(f"FAILED: Missing mandatory report: {json_path}")
            exit(1)
        if not md_path.exists():
            print(f"FAILED: Missing mandatory report: {md_path}")
            exit(1)
            
        with open(json_path) as f:
            data = json.load(f)
            if not check_finite(data):
                print(f"FAILED: Non-finite values in {json_path}")
                exit(1)
            
            # Security checks
            if "final_verdict" in data and "VALIDATED" in data["final_verdict"]:
                print(f"FAILED: Forbidden verdict 'VALIDATED' in {json_path}")
                exit(1)
            
            if "recommended_next_step" in data:
                forbidden_steps = ["preregistration", "paper live", "real trading"]
                for step in forbidden_steps:
                    if step in data["recommended_next_step"].lower():
                        print(f"FAILED: Forbidden next step '{step}' in {json_path}")
                        exit(1)

    # Consistency check report details
    consist_path = report_dir / f"microstructure_quality_mask_consistency_check_{v_norm}.json"
    with open(consist_path) as f:
        c = json.load(f)
        if c.get("version") != version:
            print(f"FAILED: Version mismatch in consistency check. Expected {version}, got {c.get('version')}")
            exit(1)
        if c.get("previous_base") != "V1.51":
            print(f"FAILED: previous_base mismatch. Expected V1.51, got {c.get('previous_base')}")
            exit(1)
        if c.get("consistency_check_status") != "MICROSTRUCTURE_QUALITY_MASK_REPORTS_CONSISTENT_RESEARCH_ONLY":
            print("FAILED: Consistency status incorrect")
            exit(1)
        
        # New mandatory flags for V1.51.1
        mandatory_flags = [
            "missing_required_reports_fixed",
            "input_guard_report_present",
            "quality_mask_recommendation_report_present",
            "project_state_aligned",
            "latest_metrics_aligned",
            "latest_summary_aligned",
            "required_reports_present",
            "required_markdown_reports_present",
            "no_strategy_validated",
            "no_preregistration_yet",
            "no_paper_live",
            "no_real_trading"
        ]
        for flag in mandatory_flags:
            if c.get(flag) is not True:
                print(f"FAILED: Mandatory flag '{flag}' must be true in consistency check")
                exit(1)

    print("VALIDATION PASSED")

if __name__ == "__main__":
    main()
