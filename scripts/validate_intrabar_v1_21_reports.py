"""Consistency validator for Galapagos V1.21 reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate_v1_21_reports(version: str = "v1.21"):
    v_norm = version.replace(".", "_")
    reports_dir = Path("reports/research")
    
    if version in ["v1.21.3", "v1.21.4", "v1.21.5"]:
        required_reports = [
            f"intrabar_data_quality_{v_norm}.json",
            f"intrabar_data_lineage_{v_norm}.json",
            f"intrabar_gap_impact_{v_norm}.json",
            f"trade_policy_comparison_{v_norm}.json",
            f"trade_ledger_intrabar_eval_{v_norm}.json",
            f"{v_norm}_recommendation.json"
        ]
    else:
        required_reports = [
            f"intrabar_coverage_plan_{v_norm}.json",
            f"intrabar_history_download_{v_norm}.json",
            f"intrabar_data_quality_{v_norm}.json",
            f"intrabar_data_lineage_{v_norm}.json",
            f"trade_ledger_intrabar_eval_{v_norm}.json",
            f"trade_policy_comparison_{v_norm}.json",
            "v_norm_recommendation.json".replace("v_norm", v_norm)
        ]
    
    if version in ["v1.21.1", "v1.21.2", "v1.21.3", "v1.21.4", "v1.21.5"]:
        required_reports.append(f"intrabar_gap_impact_{v_norm}.json")
    
    if version in ["v1.21", "v1.21.1", "v1.21.2"]:
        required_reports.append(f"intrabar_coverage_plan_{v_norm}.json")
        required_reports.append(f"intrabar_history_download_{v_norm}.json")
        required_reports.append(f"intrabar_coverage_comparison_{v_norm}.json")
    
    issues = []
    warnings = []
    missing_reports = []
    checked_reports = []
    
    # 1. Existence check
    for r in required_reports:
        if not (reports_dir / r).exists():
            issues.append(f"Missing required report: {r}")
            missing_reports.append(r)
        else:
            checked_reports.append(r)
            
    if issues:
        # Save preliminary if possible or just return
        res_fail = {
            "status": "INTRABAR_REPORTS_INCONSISTENT", 
            "version": version,
            "issues": issues,
            "missing_reports": missing_reports
        }
        with open(reports_dir / f"intrabar_{v_norm}_consistency_check.json", "w") as f:
            json.dump(res_fail, f, indent=2)
        return res_fail
        
    # 2. File standard check
    standard_file = "history_5m_v1_21.parquet"
    
    # Check quality for gaps
    has_gaps = False
    with open(reports_dir / f"intrabar_data_quality_{v_norm}.json") as f:
        quality = json.load(f)
        if quality.get("status") == "INTRABAR_DATA_HAS_GAPS":
            has_gaps = True
            warnings.append("data_has_gaps")
            if quality.get("usable_for_continuous_backtest"):
                 issues.append("Gap detected but usable_for_continuous_backtest is not false")

    # Check lineage
    with open(reports_dir / f"intrabar_data_lineage_{v_norm}.json") as f:
        lineage = json.load(f)
        if standard_file not in lineage.get("intrabar_file_path", ""):
            issues.append(f"Lineage report does not reference {standard_file}")
        if has_gaps and lineage.get("lineage_status") == "INTRABAR_LINEAGE_OK":
            issues.append("Gap detected but lineage status is plain INTRABAR_LINEAGE_OK")
            
    # Check eval
    policy_comparison_valid = "unknown"
    ready_for_reviewer = True
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.json") as f:
        eval_data = json.load(f)
        if standard_file not in eval_data.get("intrabar_metadata", {}).get("file_path", ""):
            issues.append(f"Eval report does not reference {standard_file}")
        
        ratio = eval_data.get("evaluated_ratio", 0)
        # Fallback for older formats or if ratio is missing at root
        if ratio == 0 and "ratio" in eval_data:
             ratio = eval_data["ratio"]

        if ratio < 0.20:
            issues.append(f"Evaluated ratio {ratio:.2%} is below target 20%")
        
        policy_comparison_valid = eval_data.get("comparison", {}).get("policy_comparison_valid")
        ready_for_reviewer = eval_data.get("ready_for_reviewer", True)
        
        if ratio >= 0.20:
            if has_gaps:
                if policy_comparison_valid != "preliminary_gap_aware":
                    issues.append(f"Validity mismatch for gaps: {policy_comparison_valid}")
            else:
                if policy_comparison_valid != "preliminary":
                    issues.append(f"Validity mismatch without gaps: {policy_comparison_valid}")

        if ready_for_reviewer is not False:
            issues.append("ready_for_reviewer should be false")

    # Check gap impact metrics
    gap_metrics_present = False
    if version in ["v1.21.2", "v1.21.3", "v1.21.4", "v1.21.5"]:
        with open(reports_dir / f"intrabar_gap_impact_{v_norm}.json") as f:
            gap_impact = json.load(f)
            if "raw_prediction_rows_in_gap" in gap_impact and \
               "unique_signal_timestamps_in_gap" in gap_impact:
                gap_metrics_present = True
            else:
                issues.append("Gap impact missing mandatory metrics")

    # Check standalone comparison JSON
    trade_policy_comparison_json_present = False
    with open(reports_dir / f"trade_policy_comparison_{v_norm}.json") as f:
        comp_json = json.load(f)
        trade_policy_comparison_json_present = True
        if comp_json.get("policy_comparison_valid") != policy_comparison_valid:
             issues.append("Standalone comparison valid mismatch")
        if comp_json.get("continuous_backtest_valid") is not False and has_gaps:
             issues.append("Standalone continuous_backtest_valid should be false")

    # 3. Consistency of metrics (rows, etc)
    rows_lineage = lineage.get("rows")
    rows_eval = eval_data.get("intrabar_metadata", {}).get("rows")
    if rows_lineage != rows_eval:
        issues.append(f"Row count mismatch: lineage={rows_lineage}, eval={rows_eval}")
        
    status = "INTRABAR_REPORTS_CONSISTENT"
    if has_gaps:
        status = "INTRABAR_REPORTS_CONSISTENT_GAP_AWARE"
    if issues:
        status = "INTRABAR_REPORTS_INCONSISTENT"

    result = {
        "status": status,
        "version": version,
        "issues": issues,
        "warnings": warnings,
        "required_reports": required_reports,
        "checked_reports": checked_reports,
        "missing_reports": missing_reports,
        "policy_comparison_valid": policy_comparison_valid,
        "continuous_backtest_valid": not has_gaps,
        "ready_for_reviewer": ready_for_reviewer,
        "gap_metrics_present": gap_metrics_present,
        "trade_policy_comparison_json_present": trade_policy_comparison_json_present,
        "metrics": {
            "evaluated_ratio": eval_data.get("evaluated_ratio"),
            "target_reached": eval_data.get("target_reached"),
            "rows": rows_lineage,
            "has_gaps": has_gaps
        }
    }
    
    with open(reports_dir / f"intrabar_{v_norm}_consistency_check.json", "w") as f:
        json.dump(result, f, indent=2)
        
    with open(reports_dir / f"intrabar_{v_norm}_consistency_check.md", "w") as f:
        f.write(f"# Intrabar {version} Consistency Check\n\n")
        f.write(f"- **Status**: `{result['status']}`\n")
        f.write(f"- **Policy Comparison Valid**: `{result['policy_comparison_valid']}`\n")
        f.write(f"- **Continuous Backtest Valid**: `{result['continuous_backtest_valid']}`\n")
        f.write(f"- **Ready for Reviewer**: `{result['ready_for_reviewer']}`\n")
        
        if issues:
            f.write("## Issues Found\n")
            for i in issues:
                f.write(f"- {i}\n")
        if warnings:
            f.write("## Warnings\n")
            for w in warnings:
                f.write(f"- {w}\n")
        
        if not issues:
            f.write("## Metrics Summary\n")
            f.write(f"- **Evaluated Ratio**: {result['metrics']['evaluated_ratio']:.2%}\n")
            f.write(f"- **Target Reached (20%)**: {result['metrics']['target_reached']}\n")
            f.write(f"- **Total Rows**: {result['metrics']['rows']}\n")
            f.write(f"- **Gaps Detected**: {result['metrics']['has_gaps']}\n")
            f.write(f"- **Gap Metrics Present**: {result['gap_metrics_present']}\n")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.21.1")
    args = parser.parse_args()
    res = validate_v1_21_reports(args.version)
    v_norm = args.version.replace('.', '_')
    print(f"Consistency report: reports/research/intrabar_{v_norm}_consistency_check.json")
