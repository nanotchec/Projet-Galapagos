"""Script to plan intrabar coverage expansion."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from _bootstrap import bootstrap_src_path
    bootstrap_src_path()
except ImportError:
    pass

from galapagos.research.intrabar.coverage_planner import plan_coverage


def main():
    parser = argparse.ArgumentParser(description="Plan intrabar coverage expansion.")
    parser.add_argument("--predictions", required=True, help="Path to ML predictions parquet")
    parser.add_argument("--intrabar", help="Path to current intrabar parquet file")
    parser.add_argument("--intrabar-root", help="Path to current intrabar data root")
    parser.add_argument("--target-ratio", type=float, default=0.20, help="Target coverage ratio")
    parser.add_argument("--version", default="v1.20", help="Version tag")
    
    args = parser.parse_args()
    
    # Locate current sample if exists
    intrabar_path = args.intrabar
    if not intrabar_path and args.intrabar_root:
        potential_sample = Path(args.intrabar_root) / "sample.parquet"
        if potential_sample.exists():
            intrabar_path = str(potential_sample)
            
    result = plan_coverage(args.predictions, intrabar_path, args.version)
    result["plan"]["target_ratio"] = args.target_ratio
    result["plan"]["target_evaluated_count"] = int(result["plan"]["total_candidates"] * args.target_ratio)
    
    # Save reports
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    v_norm = args.version.replace(".", "_")
    json_path = reports_dir / f"intrabar_coverage_plan_{v_norm}.json"
    md_path = reports_dir / f"intrabar_coverage_plan_{v_norm}.md"
    
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
        
    with open(md_path, "w") as f:
        f.write(f"# Intrabar Coverage Plan - {args.version}\n\n")
        f.write(f"- **Status**: `{result['status']}`\n")
        f.write(f"- **Total Candidates**: {result['plan']['total_candidates']}\n")
        
        curr = result['current_state']
        f.write("## Current State\n")
        f.write(f"- **Intrabar Min**: {curr['intrabar_min']}\n")
        f.write(f"- **Intrabar Max**: {curr['intrabar_max']}\n")
        f.write(f"- **Days**: {curr['days']}\n")
        f.write(f"- **Covered Candidates**: {curr['covered_candidates']}\n")
        f.write(f"- **Evaluated Ratio**: {curr['evaluated_ratio']:.2%}\n\n")
        
        plan = result['plan']
        f.write("## Extension Plan\n")
        f.write(f"- **Signal Range**: {plan['signal_range_min']} to {plan['signal_range_max']}\n")
        f.write(
            f"- **Recommended Range**: {plan['recommended_range']['start']} "
            f"to {plan['recommended_range']['end']}\n"
        )
        f.write(f"- **Estimated Disk Size**: {plan['estimate_disk_mb']:.1f} MB\n\n")
        
        f.write("## Target Coverage\n")
        for k, v in plan['targets'].items():
            f.write(f"- **{k}**: {v} candidates\n")

    print(f"Plan generated: {md_path}")

if __name__ == "__main__":
    main()
