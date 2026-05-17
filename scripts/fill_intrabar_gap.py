"""Script to fill intrabar gaps for V1.22."""
from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from galapagos.research.intrabar.gap_downloader import fill_planned_chunks, merge_and_save
from galapagos.research.intrabar.gap_fill_planner import generate_gap_fill_plan

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Fill Intrabar Gaps")
    parser.add_argument("--source", default="binance", help="Data source")
    parser.add_argument("--symbol", default="BTCUSDT", help="Symbol")
    parser.add_argument("--timeframe", default="5m", help="Timeframe")
    parser.add_argument("--input", required=True, help="Input parquet path")
    parser.add_argument("--output", required=True, help="Output parquet path")
    parser.add_argument("--version", default="v1.22", help="Version tag")
    parser.add_argument("--max-chunks", type=int, default=48, help="Max chunks to download")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--target-start", help="Target start date (ISO)")
    parser.add_argument("--target-end", help="Target end date (ISO)")
    parser.add_argument("--reuse-existing", action="store_true", help="Reuse existing file and generate report")
    
    args = parser.parse_args()
    
    t_start = datetime.fromisoformat(args.target_start) if args.target_start else None
    t_end = datetime.fromisoformat(args.target_end) if args.target_end else None

    print(f"--- Galapagos {args.version} Gap Downloader ---")
    
    # 1. Plan
    if args.reuse_existing:
        print("Reusing existing file as requested.")
        final_df = pd.read_parquet(args.input)
        results = []
        plan = {"total_rows": len(final_df), "gaps_count": 0, "planned_chunks": []}
    else:
        plan = generate_gap_fill_plan(
            args.input, version=args.version,
            target_start=t_start, target_end=t_end
        )
        if not plan["planned_chunks"]:
            print("No chunks planned. Dataset might be complete.")
            # Still generate report if requested
            final_df = pd.read_parquet(args.input)
            results = []
        else:
            print(f"Planned {len(plan['planned_chunks'])} chunks to fill gap.")
            # 2. Download
            results = fill_planned_chunks(
                args.source, args.symbol, args.timeframe,
                plan["planned_chunks"], max_chunks=args.max_chunks,
                dry_run=args.dry_run
            )
            # 3. Merge and Save
            final_df = merge_and_save(args.input, args.output, results, dry_run=args.dry_run)
    
    # 4. Report
    v_norm = args.version.replace(".", "_")
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = reports_dir / f"intrabar_gap_fill_download_{v_norm}.json"
    md_path = reports_dir / f"intrabar_gap_fill_download_{v_norm}.md"
    
    summary = {
        "version": args.version,
        "dry_run": args.dry_run,
        "input_path": args.input,
        "output_path": args.output,
        "chunks_attempted": len(results),
        "chunks_successful": sum(1 for r in results if r["status"] in ["success", "dry_run_success"]),
        "rows_before": plan["total_rows"],
        "rows_after": len(final_df),
        "first_timestamp": final_df["timestamp"].min().isoformat() if not final_df.empty else None,
        "last_timestamp": final_df["timestamp"].max().isoformat() if not final_df.empty else None,
        "generated_at": datetime.now(UTC).isoformat()
    }
    
    # Simplified gap analysis for status
    diffs = final_df["timestamp"].diff()
    expected_delta = pd.Timedelta(args.timeframe if args.timeframe != "5m" else "5min")
    gaps_count = len(final_df.index[diffs > expected_delta])
    
    if gaps_count == 0:
        summary["status"] = "GAP_FILLED"
    elif gaps_count < plan["gaps_count"]:
        summary["status"] = "GAP_PARTIALLY_FILLED"
    else:
        summary["status"] = "GAP_FILL_FAILED"
        
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    md_lines = [
        f"# Intrabar Gap Fill Download - {args.version}",
        "",
        f"- **Status**: `{summary['status']}`",
        f"- **Dry Run**: {summary['dry_run']}",
        f"- **Rows Before**: {summary['rows_before']}",
        f"- **Rows After**: {summary['rows_after']}",
        f"- **Chunks Successful**: {summary['chunks_successful']}/{summary['chunks_attempted']}",
        ""
    ]
    md_path.write_text("\n".join(md_lines))
    
    print(f"Download report: {json_path}")
    print(f"Final status: {summary['status']}")

if __name__ == "__main__":
    main()
