"""Script to extend historical intrabar data."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

try:
    from _bootstrap import bootstrap_src_path
    bootstrap_src_path()
except ImportError:
    pass

from galapagos.research.intrabar.history_downloader import extend_history

logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser(description="Extend historical intrabar data.")
    parser.add_argument("--source", default="binance", help="Data source")
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--timeframe", default="5m", help="Timeframe")
    parser.add_argument("--days", type=int, default=None, help="Total days of history requested")
    parser.add_argument("--target-ratio", type=float, help="Target coverage ratio (reads plan)")
    parser.add_argument("--max-chunks", type=int, default=12, help="Max API calls to make")
    parser.add_argument("--version", default="v1.20", help="Version tag")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    
    args = parser.parse_args()
    
    v_norm = args.version.replace(".", "_")
    
    # If target-ratio is provided, try to read the plan
    days = args.days
    if args.target_ratio:
        plan_path = Path(f"reports/research/intrabar_coverage_plan_{v_norm}.json")
        if plan_path.exists():
            with open(plan_path) as f:
                plan_data = json.load(f)
            # Rough estimate: we need to reach target ratio.
            # Current: 41 days -> 5%. Target 20% -> need ~160 days total.
            # We'll use the recommended range in plan if possible.
            rec = plan_data.get("plan", {}).get("recommended_range", {})
            if rec:
                end_dt = pd.to_datetime(rec["end"])
                start_dt = pd.to_datetime(rec["start"])
                days = (end_dt - start_dt).days
                logging.info(f"Target ratio {args.target_ratio} requested. Using plan recommended {days} days.")
        
    if days is None:
        days = 180 # Default
        
    output_path = (
        f"data/silver/intrabar/{args.source}/{args.symbol}/{args.timeframe}/"
        f"history_5m_{v_norm}.parquet"
    )
    
    result = extend_history(
        source=args.source,
        symbol=args.symbol,
        timeframe=args.timeframe,
        days=days,
        output_path=output_path,
        max_chunks=args.max_chunks,
        dry_run=args.dry_run,
        version=args.version
    )
    
    # Save report
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)
    v_norm = args.version.replace(".", "_")
    json_path = reports_dir / f"intrabar_history_download_{v_norm}.json"
    md_path = reports_dir / f"intrabar_history_download_{v_norm}.md"
    
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
        
    with open(md_path, "w") as f:
        f.write(f"# Intrabar History Download - {args.version}\n\n")
        f.write(f"- **Status**: `{result['status']}`\n")
        f.write(f"- **Dry Run**: `{result.get('dry_run', False)}`\n")
        if result.get('dry_run'):
            f.write(f"- **Requested Days**: {args.days}\n")
        else:
            f.write(f"- **Rows**: {result.get('rows', 0)}\n")
            f.write(f"- **Range**: {result.get('first_timestamp')} to {result.get('last_timestamp')}\n")
            f.write(f"- **Chunks Successful**: {result.get('chunks_successful', 0)}\n")
            f.write(f"- **Existing File Reused**: {result.get('existing_file_reused', False)}\n")
            f.write(f"- **File Path**: `{result.get('file_path')}`\n")
            
    print(f"Download report: {md_path}")

if __name__ == "__main__":
    main()
