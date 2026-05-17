"""Script to analyze gaps and plan the fill process for V1.22."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from galapagos.research.intrabar.gap_fill_planner import generate_gap_fill_plan


def main():
    parser = argparse.ArgumentParser(description="Plan Intrabar Gap Fill")
    parser.add_argument("--intrabar", required=True, help="Path to input parquet")
    parser.add_argument("--version", default="v1.22", help="Version tag")
    parser.add_argument("--chunk-size", type=int, default=14, help="Chunk size in days")
    
    args = parser.parse_args()
    
    print(f"--- Galapagos {args.version} Gap Fill Planner ---")
    print(f"Analyzing: {args.intrabar}")
    
    plan = generate_gap_fill_plan(args.intrabar, version=args.version, chunk_size_days=args.chunk_size)
    
    # Save reports
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    v_norm = args.version.replace(".", "_")
    json_path = reports_dir / f"intrabar_gap_fill_plan_{v_norm}.json"
    md_path = reports_dir / f"intrabar_gap_fill_plan_{v_norm}.md"
    
    with open(json_path, "w") as f:
        json.dump(plan, f, indent=2)
    
    # Generate Markdown report
    md_lines = [
        f"# Intrabar Gap Fill Plan - {args.version}",
        "",
        f"- **Input File**: `{plan['input_file']}`",
        f"- **Total Rows**: {plan['total_rows']}",
        f"- **Status**: `{plan['status']}`",
        f"- **Gaps Count**: {plan['gaps_count']}",
        ""
    ]
    
    if "largest_gap" in plan:
        lg = plan["largest_gap"]
        md_lines.extend([
            "## Largest Gap Details",
            f"- **Start**: {lg['start']}",
            f"- **End**: {lg['end']}",
            f"- **Duration**: {lg['duration_str']}",
            f"- **Expected Rows (5m)**: {lg['expected_rows']}",
            ""
        ])
        
    if plan["planned_chunks"]:
        md_lines.extend([
            "## Planned Chunks",
            f"Total chunks: {len(plan['planned_chunks'])}",
            "",
            "| Chunk | Start | End | Status |",
            "|---|---|---|---|",
        ])
        for i, c in enumerate(plan["planned_chunks"]):
            md_lines.append(f"| {i+1} | {c['start']} | {c['end']} | {c['status']} |")
            
    md_path.write_text("\n".join(md_lines))
    
    print(f"Plan generated: {json_path}")
    print(f"Status: {plan['status']}")
    if "largest_gap" in plan:
        print(f"Largest Gap: {plan['largest_gap']['duration_str']}")
    print(f"Chunks planned: {len(plan['planned_chunks'])}")

if __name__ == "__main__":
    main()
