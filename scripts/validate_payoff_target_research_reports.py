"""Validator for V1.42.3 research reports."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from _bootstrap import bootstrap_src_path
bootstrap_src_path()

def check_for_nan_inf(data: any) -> bool:
    """Recursively check for NaN or Infinity in JSON-like data."""
    if isinstance(data, dict):
        return any(check_for_nan_inf(v) for v in data.values())
    elif isinstance(data, list):
        return any(check_for_nan_inf(x) for x in data)
    elif isinstance(data, float):
        import math
        return math.isnan(data) or math.isinf(data)
    return False

def validate_reports(version: str = "v1.42.3"):
    version_norm = version.lower().replace(".", "_")
    summary_path = Path(f"reports/research/payoff_target_research_summary_{version_norm}.json")
    if not summary_path.exists():
        print(f"Error: {summary_path} missing")
        return False
        
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    
    issues = []
    
    # 1. Base checks
    if summary.get("version") != version.upper():
        issues.append(f"Summary version mismatch: {summary.get('version')} != {version.upper()}")
    if summary.get("failure_diagnostic_base") != "V1.41":
        issues.append("failure_diagnostic_base must be V1.41")
    if summary.get("payoff_objective_base_version") != "V1.40.1":
        issues.append("payoff_objective_base_version must be V1.40.1")
    if summary.get("diagnostic_base") != "V1.39":
        issues.append("diagnostic_base must be V1.39")
    if summary.get("canonical_base_version") != "V1.37.2":
        issues.append("canonical_base_version must be V1.37.2")
        
    # 2. Safety checks
    if summary.get("evidence_classification") != "EXPLORATORY_ONLY":
        issues.append("evidence_classification must be EXPLORATORY_ONLY")
    if summary.get("no_new_filter") is not True:
        issues.append("no_new_filter must be true")
    if summary.get("no_strategy_validated") is not True:
        issues.append("no_strategy_validated must be true")
    if summary.get("no_paper_live") is not True:
        issues.append("no_paper_live must be true")
    if summary.get("no_real_trading") is not True:
        issues.append("no_real_trading must be true")
        
    # 3. Metric alignment checks
    if summary.get("final_verdict") == "PAYOFF_TARGET_RESEARCH_PROMISING_BUT_UNVALIDATED":
        issues.append("Stale promising verdict detected")
    if summary.get("best_target_observed") == "net_return_regression":
        issues.append("Stale best_target_observed detected (must be null for label-only)")
    if summary.get("beats_v1_40_1_target") is True:
        issues.append("Stale beats_v1_40_1_target detected (must be false for label-only)")
    if summary.get("best_target_observed") is not None:
        issues.append(f"best_target_observed must be null in {version.upper()}")

    # 4. Integrity checks
    if summary.get("json_finiteness_status") != "PAYOFF_TARGET_JSON_FINITE_PASSED":
        issues.append("JSON finiteness audit failed (NaN/Inf detected in summary field)")
    
    # Walk-forward clarified fields check
    wf_path = Path(f"reports/research/payoff_target_horizon_walk_forward_eval_{version_norm}.json")
    if wf_path.exists():
        wf = json.loads(wf_path.read_text(encoding="utf-8"))
        if wf.get("raw_nan_values_remaining", -1) != 0:
            issues.append("raw_nan_values_remaining must be 0")
        if wf.get("raw_infinity_values_remaining", -1) != 0:
            issues.append("raw_infinity_values_remaining must be 0")
        if wf.get("all_json_values_finite") is not True:
            issues.append("all_json_values_finite must be true")

    # Check all research JSONs for NaN/Inf
    for p in Path("reports/research").glob(f"*{version_norm}.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if check_for_nan_inf(data):
                issues.append(f"NaN or Infinity detected in {p.name}")
        except Exception as e:
            issues.append(f"Could not audit {p.name}: {e}")

    # 5. Report presence
    required_reports = [
        f"payoff_target_input_guard_{version_norm}.json",
        f"payoff_target_count_semantics_{version_norm}.json",
        f"payoff_target_horizon_candidates_{version_norm}.json",
        f"payoff_target_definitions_{version_norm}.json",
        f"payoff_target_noise_analysis_{version_norm}.json",
        f"payoff_downside_label_analysis_{version_norm}.json",
        f"payoff_target_horizon_walk_forward_eval_{version_norm}.json",
        f"payoff_target_baseline_comparison_{version_norm}.json",
        f"payoff_target_temporal_robustness_{version_norm}.json",
        f"payoff_target_regime_breakdown_{version_norm}.json",
        f"payoff_target_overfit_guard_{version_norm}.json",
        f"payoff_target_json_finiteness_audit_{version_norm}.json",
        f"payoff_target_state_alignment_{version_norm}.json",
        f"{version_norm}_recommendation.json"
    ]
    for rep in required_reports:
        if not Path(f"reports/research/{rep}").exists():
            issues.append(f"Missing required report: {rep}")
            
    # 6. Global State alignment
    expected_consistency = "PAYOFF_TARGET_RESEARCH_REPORTS_CONSISTENT_STATE_ALIGNED_EXPLORATORY_ONLY"
    forbidden_consistency = "PAYOFF_TARGET_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY"

    ps_path = Path("reports/PROJECT_STATE.json")
    if ps_path.exists():
        ps = json.loads(ps_path.read_text(encoding="utf-8"))
        if ps.get("version") != version.upper():
            issues.append(f"PROJECT_STATE version mismatch: {ps.get('version')} != {version.upper()}")
        if ps.get("consistency_check_status") == forbidden_consistency:
            issues.append("PROJECT_STATE contains short consistency status")
        if ps.get("consistency_check_status") != expected_consistency:
            issues.append(f"PROJECT_STATE consistency status mismatch: expected {expected_consistency}")
        if ps.get("final_verdict") == "PAYOFF_TARGET_RESEARCH_PROMISING_BUT_UNVALIDATED":
            issues.append("PROJECT_STATE contains stale promising verdict")
        if ps.get("diagnostic_base") != "V1.39":
            issues.append(f"PROJECT_STATE diagnostic_base mismatch: {ps.get('diagnostic_base')} != V1.39")

    lm_path = Path("reports/current/latest_metrics.json")
    if lm_path.exists():
        lm = json.loads(lm_path.read_text(encoding="utf-8"))
        if lm.get("version") != version.upper():
            issues.append(f"latest_metrics version mismatch: {lm.get('version')} != {version.upper()}")
        if lm.get("consistency_check_status") != expected_consistency:
            issues.append(f"latest_metrics consistency status mismatch: expected {expected_consistency}")
        if lm.get("final_verdict") == "PAYOFF_TARGET_RESEARCH_PROMISING_BUT_UNVALIDATED":
            issues.append("latest_metrics contains stale promising verdict")

    ps_md = Path("reports/PROJECT_STATE.md")
    if ps_md.exists():
        content = ps_md.read_text(encoding="utf-8")
        if f"# Project State - {version.upper()}" not in content:
            issues.append(f"PROJECT_STATE.md title mismatch or stale: expected {version.upper()}")
        if forbidden_consistency in content:
            issues.append("PROJECT_STATE.md contains short consistency status")
        if expected_consistency not in content:
            issues.append("PROJECT_STATE.md missing full consistency status")

    ls_md = Path("reports/current/latest_summary.md")
    if ls_md.exists():
        content = ls_md.read_text(encoding="utf-8")
        if f"# Latest Summary - {version.upper()}" not in content:
            issues.append(f"latest_summary.md title mismatch or stale: expected {version.upper()}")
        if expected_consistency not in content:
            issues.append("latest_summary.md missing full consistency status")

    if issues:
        print(f"Validation FAILED for {version}:")
        for issue in issues:
            print(f"- {issue}")
        return False
        
    # Write consistency check report
    consistency = {
        "consistency_check_status": expected_consistency,
        "version": version,
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "issues": []
    }
    Path(f"reports/research/payoff_target_consistency_check_{version_norm}.json").write_text(json.dumps(consistency, indent=2))
    
    lines = [
        f"# Payoff Target Consistency Check {version}",
        "",
        f"Status: {expected_consistency}",
        "",
        "Integrity Fixes Applied:",
        "- NaN/Infinity Scan: PASSED",
        "- State Alignment: VERIFIED",
        "- Diagnostic Base Correction (V1.39): VERIFIED",
        "- Stale V1.42 Fields Removal: VERIFIED",
        "- Finiteness Clarity: VERIFIED (raw_nan == 0)"
    ]
    Path(f"reports/research/payoff_target_consistency_check_{version_norm}.md").write_text("\n".join(lines))
    
    print(f"Validation PASSED for {version}.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.42.3")
    args = parser.parse_args()
    if validate_reports(args.version):
        exit(0)
    else:
        exit(1)
