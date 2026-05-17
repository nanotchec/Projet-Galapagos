"""Validator for Microstructure Coverage Quality Audit V1.50 / V1.50.1."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

def check_finite(obj):
    """Recursively check for NaN/Inf in a JSON-like object."""
    if isinstance(obj, dict):
        return all(check_finite(v) for v in obj.values())
    elif isinstance(obj, list):
        return all(check_finite(x) for x in obj)
    elif isinstance(obj, float):
        return math.isfinite(obj)
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.50.1")
    args = parser.parse_args()
    
    version = args.version.upper()
    v_norm = version.lower().replace(".", "_")
    report_dir = Path("reports/research")
    
    mandatory_reports = [
        "microstructure_coverage_input_guard",
        "microstructure_intrabar_coverage_audit",
        "microstructure_timestamp_alignment_audit",
        "microstructure_missingness_profile",
        "microstructure_gap_detection",
        "microstructure_session_quality_profile",
        "microstructure_feature_availability",
        "microstructure_label_coverage_impact",
        "microstructure_coverage_vs_failure_analysis",
        "microstructure_quality_policy",
        "microstructure_coverage_scorecard",
        "microstructure_coverage_recommendation",
        "microstructure_coverage_quality_summary",
        "microstructure_coverage_quality_consistency_check",
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
            print(f"FAILED: Missing {json_path}")
            exit(1)
        if not md_path.exists():
            print(f"FAILED: Missing {md_path}")
            exit(1)
            
        with open(json_path) as f:
            data = json.load(f)
            if not check_finite(data):
                print(f"FAILED: Non-finite values in {json_path}")
                exit(1)
                
    # Check consistency report specifically
    consist_path = report_dir / f"microstructure_coverage_quality_consistency_check_{v_norm}.json"
    with open(consist_path) as f:
        c = json.load(f)
        if c.get("version") != version:
            print(f"FAILED: Wrong version in consistency check: {c.get('version')}")
            exit(1)
            
        expected_prev = "V1.50" if version == "V1.50.1" else "V1.49.1"
        if c.get("previous_base") != expected_prev:
            print(f"FAILED: previous_base must be {expected_prev}, got {c.get('previous_base')}")
            exit(1)
            
        if c.get("consistency_check_status") != "MICROSTRUCTURE_COVERAGE_QUALITY_REPORTS_CONSISTENT_RESEARCH_ONLY":
            print("FAILED: Wrong consistency status")
            exit(1)
        if c.get("issues") != []:
            print("FAILED: issues must be empty")
            exit(1)
            
        for field in [
            "project_state_aligned", "latest_metrics_aligned", "latest_summary_aligned",
            "latest_previous_base_aligned", "release_ready_consistent",
            "all_json_values_finite", "required_reports_present", "required_markdown_reports_present",
            "safety_flags_aligned", "recommendation_aligned", "release_reports_present",
            "final_verdict_aligned", "recommended_next_step_aligned"
        ]:
            if c.get(field) is not True:
                print(f"FAILED: {field} must be true in consistency check")
                exit(1)
                
        for flag in ["no_strategy_validated", "no_preregistration_yet", "no_paper_live", "no_real_trading"]:
            if c.get(flag) is not True:
                print(f"FAILED: {flag} must be true")
                exit(1)
        if c.get("holdout_executed") is not False:
            print("FAILED: holdout_executed must be false")
            exit(1)
        if c.get("real_orders_possible") is not False:
            print("FAILED: real_orders_possible must be false")
            exit(1)
            
    # Check Summary for forbidden terms
    summary_path = report_dir / f"microstructure_coverage_quality_summary_{v_norm}.json"
    with open(summary_path) as f:
        s = json.load(f)
        verdict = s.get("final_verdict", "")
        if "VALIDATED" in verdict:
            print("FAILED: Verdict contains VALIDATED")
            exit(1)
        next_step = s.get("recommended_next_step", "")
        for forbidden in ["preregistration", "paper live", "real trading"]:
            if forbidden in next_step.lower():
                print(f"FAILED: Next step contains forbidden term: {forbidden}")
                exit(1)

    # PROJECT_STATE / latest alignment
    ps_path = Path("reports/PROJECT_STATE.json")
    with open(ps_path) as f:
        ps = json.load(f)
        if ps.get("version") != version:
            print(f"FAILED: PROJECT_STATE version mismatch: {ps.get('version')}")
            exit(1)
        if ps.get("previous_base") != expected_prev:
            print(f"FAILED: PROJECT_STATE previous_base mismatch: {ps.get('previous_base')}")
            exit(1)

    metrics_path = Path("reports/current/latest_metrics.json")
    with open(metrics_path) as f:
        lm = json.load(f)
        if lm.get("current_version") != version:
            print(f"FAILED: latest_metrics current_version mismatch: {lm.get('current_version')}")
            exit(1)
        if lm.get("previous_version") != expected_prev:
            print(f"FAILED: latest_metrics previous_version mismatch: {lm.get('previous_version')}")
            exit(1)
        if lm.get("previous_base") != expected_prev:
            print(f"FAILED: latest_metrics previous_base mismatch: {lm.get('previous_base')}")
            exit(1)

    # Release report consistency (if it exists)
    release_path = Path(f"reports/release_zip_{v_norm}.json")
    if release_path.exists():
        with open(release_path) as f:
            rel = json.load(f)
            checks = [
                "final_audit_passed", "final_smoke_passed", "final_consistency_passed"
            ]
            all_green = all(rel.get(c) is True for c in checks)
            no_issues = rel.get("final_missing_required_files") == [] and \
                        rel.get("final_forbidden_count") == 0 and \
                        rel.get("final_secret_hits") == []
            
            if all_green and no_issues:
                if rel.get("release_ready_for_external_review") is not True:
                    print("FAILED: release_ready_for_external_review should be true when all checks pass")
                    exit(1)
            elif rel.get("release_ready_for_external_review") is False:
                if not rel.get("issues") and not rel.get("blocking_reason"):
                    print("FAILED: release_ready_for_external_review is false without issues/blocking_reason")
                    exit(1)

    print("VALIDATION PASSED")

if __name__ == "__main__":
    main()
