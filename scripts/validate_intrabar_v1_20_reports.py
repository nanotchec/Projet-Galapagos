"""Global consistency validator for V1.20+ intrabar reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from galapagos.research.report_models import write_research_report


def validate_reports(version: str, reports_dir: Path | None = None) -> dict[str, Any]:
    v_norm = version.replace(".", "_")
    if reports_dir is None:
        reports_dir = Path("reports/research")
    
    download_path = reports_dir / f"intrabar_history_download_{v_norm}.json"
    quality_path = reports_dir / f"intrabar_data_quality_{v_norm}.json"
    lineage_path = reports_dir / f"intrabar_data_lineage_{v_norm}.json"
    eval_path = reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.json"
    
    issues = []
    
    # 1. Existence checks
    for p in [download_path, quality_path, lineage_path, eval_path]:
        if not p.exists():
            issues.append(f"Missing report: {p.name}")
            
    if issues:
        return {
            "status": "INTRABAR_REPORTS_INCONSISTENT",
            "issues": issues,
            "version": version
        }
        
    # 2. Loading
    with open(download_path) as f:
        dl = json.load(f)
    with open(quality_path) as f:
        q = json.load(f)
    with open(lineage_path) as f:
        lin = json.load(f)
    with open(eval_path) as f:
        ev = json.load(f)
    
    # 3. Cross-checks
    
    # Rows consistency
    lin_rows = lin.get("rows")
    q_rows = q.get("rows")
    if lin_rows != q_rows:
        issues.append(f"Row mismatch: Lineage={lin_rows}, Quality={q_rows}")
        
    # Timestamps consistency
    if lin.get("first_timestamp") != q.get("start_time"):
        # Note: sometimes isoformat vs string might differ slightly, but we expect exact match here
        issues.append(
            f"Start timestamp mismatch: Lineage={lin.get('first_timestamp')}, "
            f"Quality={q.get('start_time')}"
        )
        
    # Eval source check
    eval_meta = ev.get("intrabar_metadata", {})
    if eval_meta.get("rows") != lin_rows:
        issues.append(f"Eval row mismatch: Eval={eval_meta.get('rows')}, Lineage={lin_rows}")
        
    # Download status honesty
    if dl.get("status") == "dry_run" and ev.get("intrabar_metadata"):
        issues.append("Download report claims dry_run but Evaluation used data")
        
    # Evaluated ratio logic
    policy_metrics = ev.get("policy_metrics", {})
    ratios = [m.get("evaluated_ratio", 0) for m in policy_metrics.values()]
    avg_ratio = sum(ratios) / len(ratios) if ratios else 0
    
    comparison = ev.get("comparison", {})
    valid = comparison.get("policy_comparison_valid")
    if avg_ratio < 0.2 and valid:
        issues.append(f"Comparison valid=True but coverage={avg_ratio:.2%} < 20%")
        
    # Ready for reviewer check
    if ev.get("ready_for_reviewer"):
        issues.append("ready_for_reviewer is True (should be False)")
        
    status = "INTRABAR_REPORTS_CONSISTENT" if not issues else "INTRABAR_REPORTS_INCONSISTENT"
    
    return {
        "status": status,
        "version": version,
        "issues": issues,
        "metrics": {
            "evaluated_ratio": avg_ratio,
            "lineage_rows": lin_rows,
            "quality_status": q.get("status")
        }
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.20.1")
    args = parser.parse_args()
    
    result = validate_reports(args.version)
    
    v_norm = args.version.replace(".", "_")
    report_name = f"intrabar_{v_norm}_consistency_check"
    
    write_research_report(
        name=report_name,
        payload=result,
        title=f"Intrabar Report Consistency Check - {args.version}",
        lines=[
            f"- **Status**: `{result['status']}`",
            f"- **Evaluated Ratio**: {result['metrics'].get('evaluated_ratio', 0):.2%}",
            f"- **Issues Found**: {len(result.get('issues', []))}",
        ] + [f"  - {iss}" for iss in result.get('issues', [])],
        output_dir="reports/research"
    )
    
    print(f"Consistency report: reports/research/{report_name}.json")

if __name__ == "__main__":
    main()
