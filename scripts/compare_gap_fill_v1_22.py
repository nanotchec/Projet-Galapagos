"""Script to compare gap fill results between V1.21.5 and V1.22."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from galapagos.research.intrabar.gap_fill_comparison import (
    compare_gap_impact,
    compare_ledger_metrics,
)


def main():
    parser = argparse.ArgumentParser(description="Compare Gap Fill results")
    parser.add_argument("--previous", required=True, help="Path to V1.21.5 gap impact JSON")
    parser.add_argument("--current", required=True, help="Path to V1.22 gap impact JSON")
    parser.add_argument("--previous-ledger", required=True, help="Path to V1.21.5 trade ledger JSON")
    parser.add_argument("--current-ledger", required=True, help="Path to V1.22 trade ledger JSON")
    parser.add_argument("--version", default="v1.22", help="Version tag")
    
    args = parser.parse_args()
    
    print(f"--- Galapagos {args.version} Gap Fill Comparison ---")
    
    with open(args.previous) as f:
        prev_impact = json.load(f)
    with open(args.current) as f:
        curr_impact = json.load(f)
    with open(args.previous_ledger) as f:
        prev_ledger = json.load(f)
    with open(args.current_ledger) as f:
        curr_ledger = json.load(f)
        
    impact_comp = compare_gap_impact(prev_impact, curr_impact)
    ledger_comp = compare_ledger_metrics(prev_ledger, curr_ledger)
    
    report = {
        "version": args.version,
        "impact_comparison": impact_comp,
        "ledger_comparison": ledger_comp,
        "generated_at": datetime.now(UTC).isoformat()
    }
    
    if impact_comp["gap_ratio_reduction"] > 0.20:
        report["status"] = "GAP_FILL_SUCCESSFUL"
    elif impact_comp["gap_ratio_reduction"] > 0.05:
        report["status"] = "GAP_FILL_PARTIAL"
    else:
        report["status"] = "GAP_FILL_NO_IMPROVEMENT"
        
    reports_dir = Path("reports/research")
    v_norm = args.version.replace(".", "_")
    json_path = reports_dir / f"intrabar_gap_fill_comparison_{v_norm}.json"
    md_path = reports_dir / f"intrabar_gap_fill_comparison_{v_norm}.md"
    
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)
        
    md_lines = [
        f"# Intrabar Gap Fill Comparison - {args.version}",
        "",
        f"- **Status**: `{report['status']}`",
        "",
        "## Coverage Evolution",
        f"- **Previous Evaluated Ratio**: {ledger_comp['previous_evaluated_ratio']:.2%}",
        f"- **Current Evaluated Ratio**: {ledger_comp['current_evaluated_ratio']:.2%}",
        f"- **Coverage Increase**: +{ledger_comp['coverage_increase']:.2%}",
        "",
        "## Gap Evolution",
        f"- **Previous Gap Candidate Ratio**: {impact_comp['previous_gap_ratio']:.2%}",
        f"- **Current Gap Candidate Ratio**: {impact_comp['current_gap_ratio']:.2%}",
        f"- **Gap Ratio Reduction**: -{impact_comp['gap_ratio_reduction']:.2%}",
        "",
        "## Scientific Verdict",
        f"- **Previous Verdict**: `{ledger_comp['previous_verdict']}`",
        f"- **Current Verdict**: `{ledger_comp['current_verdict']}`",
        ""
    ]
    md_path.write_text("\n".join(md_lines))
    
    print(f"Comparison report: {json_path}")
    print(f"Status: {report['status']}")

if __name__ == "__main__":
    main()
