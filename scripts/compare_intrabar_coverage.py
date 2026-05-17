"""Script to compare intrabar coverage between two versions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Compare intrabar coverage between versions.")
    parser.add_argument("--v-prev", required=True, help="Previous version report JSON")
    parser.add_argument("--v-curr", required=True, help="Current version report JSON")
    parser.add_argument("--version", default="v1.21", help="Current version tag")
    
    args = parser.parse_args()
    
    with open(args.v_prev) as f:
        prev = json.load(f)
    with open(args.v_curr) as f:
        curr = json.load(f)
        
    # Extract metrics
    # Note: trade_ledger_intrabar_eval report has policy_metrics
    # We'll use 'fixed_percent' as a representative policy for coverage
    p_prev = list(prev.get("policy_metrics", {}).values())[0]
    p_curr = list(curr.get("policy_metrics", {}).values())[0]
    
    prev_ratio = p_prev.get("evaluated_ratio", 0)
    curr_ratio = p_curr.get("evaluated_ratio", 0)
    
    prev_count = p_prev.get("evaluated_count", 0)
    curr_count = p_curr.get("evaluated_count", 0)
    
    improvement = curr_ratio / prev_ratio if prev_ratio > 0 else float('inf')
    
    target_ratio = 0.20
    target_reached = curr_ratio >= target_ratio
    
    result = {
        "version": args.version,
        "previous_version": prev.get("version"),
        "metrics": {
            "previous_evaluated_count": prev_count,
            "current_evaluated_count": curr_count,
            "previous_evaluated_ratio": prev_ratio,
            "current_evaluated_ratio": curr_ratio,
            "improvement_factor": improvement,
            "target_ratio": target_ratio,
            "target_reached": target_reached
        },
        "verdict": "COVERAGE_TARGET_REACHED" if target_reached else "COVERAGE_IMPROVED_BUT_BELOW_TARGET"
    }
    
    reports_dir = Path("reports/research")
    v_norm = args.version.replace(".", "_")
    json_path = reports_dir / f"intrabar_coverage_comparison_{v_norm}.json"
    md_path = reports_dir / f"intrabar_coverage_comparison_{v_norm}.md"
    
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
        
    with open(md_path, "w") as f:
        f.write(f"# Intrabar Coverage Comparison - {args.version}\n\n")
        f.write(f"- **Verdict**: `{result['verdict']}`\n")
        f.write(f"- **Target Reached**: `{target_reached}`\n\n")
        
        m = result['metrics']
        f.write("| Metric | Previous ({}) | Current ({}) | Improvement |\n".format(result['previous_version'], args.version))
        f.write("|---|---:|---:|---:|\n")
        f.write("| Evaluated Count | {} | {} | x{:.2f} |\n".format(m['previous_evaluated_count'], m['current_evaluated_count'], improvement))
        f.write("| Evaluated Ratio | {:.2%} | {:.2%} | |\n".format(m['previous_evaluated_ratio'], m['current_evaluated_ratio']))
        f.write("| Target Ratio | {:.2%} | {:.2%} | |\n".format(m['target_ratio'], m['target_ratio']))

    print(f"Comparison report: {md_path}")

if __name__ == "__main__":
    main()
