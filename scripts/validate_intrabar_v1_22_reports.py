"""Validation script for V1.22 reports consistency."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def validate_v1_22_reports(version: str = "v1.22"):
    v_norm = version.replace(".", "_")
    reports_dir = Path("reports/research")
    
    if v_norm in ["v1_23", "v1_23_1"]:
        required_reports = [
            f"loss_policy_breakdown_{v_norm}.json",
            f"loss_cost_attribution_{v_norm}.json",
            f"loss_exit_reason_analysis_{v_norm}.json",
            f"{v_norm}_recommendation.json"
        ]
    else:
        required_reports = [
            f"intrabar_gap_fill_plan_{v_norm}.json",
            f"intrabar_gap_fill_download_{v_norm}.json",
            f"intrabar_data_quality_{v_norm}.json",
            f"intrabar_data_lineage_{v_norm}.json",
            f"intrabar_gap_impact_{v_norm}.json",
            f"intrabar_gap_fill_comparison_{v_norm}.json",
            f"trade_ledger_intrabar_eval_{v_norm}.json",
            f"trade_policy_comparison_{v_norm}.json",
            f"{v_norm}_recommendation.json"
        ]
    
    issues = []
    missing_reports = []
    
    for r in required_reports:
        p = reports_dir / r
        if not p.exists():
            missing_reports.append(r)
            issues.append(f"Missing required report: {r}")
            
    # Check mandatory doc
    doc_path = Path("docs/intrabar_gap_fill_v1_22.md")
    if not doc_path.exists():
        issues.append("Missing mandatory documentation: docs/intrabar_gap_fill_v1_22.md")
            
    # Consistency check
    status = "INTRABAR_REPORTS_CONSISTENT_CONTINUOUS"
    has_gaps = False
    
    if v_norm not in ["v1_23", "v1_23_1", "v1_24", "v1_24_1", "v1_25", "v1_25_1", "v1_26"]:
        # Load data quality
        quality_path = reports_dir / f"intrabar_data_quality_{v_norm}.json"
        has_gaps = True
        if quality_path.exists():
            with open(quality_path) as f:
                quality = json.load(f)
                if quality.get("gaps_count", 0) > 0:
                    status = "INTRABAR_REPORTS_CONSISTENT_GAP_AWARE"
                    has_gaps = True
                else:
                    has_gaps = False
                    
        # Load trade ledger
        ledger_path = reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.json"
        if ledger_path.exists():
            with open(ledger_path) as f:
                ledger = json.load(f)
                validity = ledger.get("comparison_valid")
                if has_gaps:
                    if validity != "preliminary_gap_aware":
                        issues.append(f"Validity mismatch: expected preliminary_gap_aware, got {validity}")
                else:
                    if validity != "preliminary_continuous":
                        issues.append(f"Validity mismatch: expected preliminary_continuous, got {validity}")
                        
                if ledger.get("ready_for_reviewer") is not False:
                    issues.append("ready_for_reviewer must be false")

        # Load lineage
        lineage_path = reports_dir / f"intrabar_data_lineage_{v_norm}.json"
        if lineage_path.exists():
            with open(lineage_path) as f:
                lineage = json.load(f)
                dp = lineage.get("download_report_path", "")
                if "intrabar_gap_fill_download" not in dp:
                    issues.append(f"Lineage mismatch: download_report_path should point to gap_fill_download, got {dp}")

        # Load gap impact
        impact_path = reports_dir / f"intrabar_gap_impact_{v_norm}.json"
        if impact_path.exists():
            with open(impact_path) as f:
                impact = json.load(f)
                tc_gap = impact.get("trade_candidates_in_gap", 0)
                tc_ratio = impact.get("trade_candidates_gap_ratio", 0)
                if tc_gap == 0 and tc_ratio != 0.0:
                    issues.append(f"Gap ratio mismatch: count is 0 but ratio is {tc_ratio}")
                
    if issues:
        status = "INTRABAR_REPORTS_INCONSISTENT"
        
    report = {
        "status": status,
        "version": version,
        "issues": issues,
        "missing_reports": missing_reports,
        "has_gaps": has_gaps,
        "generated_at": datetime.now(UTC).isoformat()
    }
    
    json_path = reports_dir / f"intrabar_{v_norm}_consistency_check.json"
    md_path = reports_dir / f"intrabar_{v_norm}_consistency_check.md"
    
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)
        
    md_lines = [
        f"# Intrabar Consistency Check - {version}",
        "",
        f"- **Status**: `{status}`",
        f"- **Gaps Detected**: {has_gaps}",
        ""
    ]
    if issues:
        md_lines.append("## Issues")
        for i in issues:
            md_lines.append(f"- {i}")
            
    md_path.write_text("\n".join(md_lines))
    print(f"Consistency report: {json_path}")
    print(f"Status: {status}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.22")
    args = parser.parse_args()
    validate_v1_22_reports(args.version)
