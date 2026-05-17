"""Validator for Microstructure Data Enrichment Spec reports (V1.52)."""
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
    parser.add_argument("--version", default="v1.52")
    args = parser.parse_args()
    
    version = args.version.upper()
    v_norm = version.lower().replace(".", "_")
    report_dir = Path("reports/research")
    
    mandatory_reports = [
        "microstructure_data_enrichment_input_guard",
        "microstructure_existing_data_inventory",
        "microstructure_coverage_gap_spec",
        "microstructure_required_field_spec",
        "microstructure_source_candidate_policy",
        "microstructure_causal_availability_spec",
        "microstructure_backfill_plan",
        "microstructure_validation_criteria",
        "microstructure_data_contract",
        "microstructure_enrichment_risk_audit",
        "microstructure_implementation_roadmap",
        "microstructure_data_enrichment_recommendation",
        "microstructure_data_enrichment_summary",
        "microstructure_data_enrichment_consistency_check",
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
            if data.get("external_data_downloaded") is True:
                print(f"FAILED: external_data_downloaded must be false in {json_path}")
                exit(1)
            if data.get("external_api_called") is True:
                print(f"FAILED: external_api_called must be false in {json_path}")
                exit(1)
            if "final_verdict" in data and "VALIDATED" in data["final_verdict"]:
                print(f"FAILED: Forbidden verdict 'VALIDATED' in {json_path}")
                exit(1)
            
            if "recommended_next_step" in data:
                forbidden_steps = ["paper live", "real trading", "preregistration"]
                for step in forbidden_steps:
                    if step in data["recommended_next_step"].lower():
                        print(f"FAILED: Forbidden next step '{step}' in {json_path}")
                        exit(1)

    # Consistency check report details
    consist_path = report_dir / f"microstructure_data_enrichment_consistency_check_{v_norm}.json"
    with open(consist_path) as f:
        c = json.load(f)
        if c.get("version") != version:
            print(f"FAILED: Version mismatch in consistency check. Expected {version}, got {c.get('version')}")
            exit(1)
        if c.get("previous_base") != "V1.51.1":
            print(f"FAILED: previous_base mismatch. Expected V1.51.1, got {c.get('previous_base')}")
            exit(1)
        if c.get("consistency_check_status") != "MICROSTRUCTURE_DATA_ENRICHMENT_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY":
            print("FAILED: Consistency status incorrect")
            exit(1)
        
        mandatory_flags = [
            "project_state_aligned",
            "latest_metrics_aligned",
            "latest_summary_aligned",
            "required_reports_present",
            "required_markdown_reports_present",
            "safety_flags_aligned",
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
