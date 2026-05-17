"""Script to audit intrabar data quality."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from _bootstrap import bootstrap_src_path
    bootstrap_src_path()
except ImportError:
    pass

from galapagos.research.intrabar.data_quality import audit_intrabar_quality


def main():
    parser = argparse.ArgumentParser(description="Audit intrabar data quality.")
    parser.add_argument("--intrabar", required=True, help="Path to intrabar parquet")
    parser.add_argument("--version", default="v1.20", help="Version tag")
    
    args = parser.parse_args()
    
    result = audit_intrabar_quality(args.intrabar)
    
    # Save reports
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    v_norm = args.version.replace(".", "_")
    json_path = reports_dir / f"intrabar_data_quality_{v_norm}.json"
    md_path = reports_dir / f"intrabar_data_quality_{v_norm}.md"
    
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
        
    with open(md_path, "w") as f:
        f.write(f"# Intrabar Data Quality Audit - {args.version}\n\n")
        f.write(f"- **Status**: `{result['status']}`\n")
        f.write(f"- **Rows**: {result['rows']}\n")
        f.write(f"- **Is Monotonic**: {result['is_monotonic']}\n")
        f.write(f"- **Duplicates**: {result['duplicates']}\n")
        f.write(f"- **OHLC Valid**: {result['ohlc_valid']}\n")
        f.write(f"- **Gaps Count**: {result['gaps_count']}\n")
        f.write(f"- **Coverage Percentage**: {result['coverage_pct']:.2%}\n")
        f.write(f"- **Usable for Continuous Backtest**: {result['usable_for_continuous_backtest']}\n")
        f.write(f"- **Usable for Gap-Aware Eval**: {result['usable_for_gap_aware_signal_eval']}\n")
        f.write(f"- **Range**: {result['start_time']} to {result['end_time']}\n\n")
        
        if result['notable_gaps']:
            f.write("## Notable Gaps\n")
            for g in result['notable_gaps']:
                f.write(f"- Between {g['after']} and {g['before']} (Gap: {g['gap']})\n")

    print(f"Quality report: {md_path}")

if __name__ == "__main__":
    main()
