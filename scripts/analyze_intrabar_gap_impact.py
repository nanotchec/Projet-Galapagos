"""Script to analyze the impact of intrabar gaps on signal evaluation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from galapagos.research.intrabar.gap_analysis import analyze_signal_gap_impact
from galapagos.research.report_models import write_research_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, help="Path to ML predictions")
    parser.add_argument("--intrabar", required=True, help="Path to intrabar data")
    parser.add_argument("--version", default="v1.21.2")
    args = parser.parse_args()

    print(f"Analyzing gap impact for {args.version}...")
    
    signals_df = pd.read_parquet(args.predictions)
    intrabar_df = pd.read_parquet(args.intrabar)
    
    result = analyze_signal_gap_impact(signals_df, intrabar_df)
    
    # Try to estimate evaluated candidates if a recent eval report exists
    # This is a heuristic as we don't load the full trade ledger here
    v_prev = "v1_21_1"
    eval_prev_path = Path("reports/research") / f"trade_ledger_intrabar_eval_{v_prev}.json"
    if eval_prev_path.exists():
        try:
            with open(eval_prev_path) as f:
                eval_data = json.load(f)
                prev_audit = eval_data.get("signal_audit", {})
                # For V1.21.1+, candidates = unique_signal_timestamps
                tc_total = prev_audit.get("unique_signal_timestamps")
                if tc_total is None:
                    tc_total = prev_audit.get("total_signals")
                
                result["trade_candidates_total"] = tc_total
                # We assume the gap ratio for candidates is similar to unique timestamps
                ug_ratio = result["unique_signal_timestamps_gap_ratio"]
                if tc_total and ug_ratio:
                    result["trade_candidates_in_gap"] = int(tc_total * ug_ratio)
                    result["trade_candidates_gap_ratio"] = ug_ratio
        except Exception:
            pass

    if result.get("trade_candidates_total") is None:
        result["trade_candidates_gap_ratio"] = None
        result["reason"] = "trade_candidates_not_loaded"

    v_v = args.version.replace(".", "_")
    report_name = f"intrabar_gap_impact_{v_v}"
    
    lines = [
        f"- **Verdict**: `{result['verdict']}`",
        "",
        "### Raw Prediction Rows",
        f"- **Total**: {result['raw_prediction_rows_total']}",
    ]
    gs_gap = result['raw_prediction_rows_in_gap']
    gs_ratio = result['raw_prediction_rows_gap_ratio']
    lines.append(f"- **In Gap**: {gs_gap} ({gs_ratio:.2%})")
    lines.extend([
        "",
        "### Unique Signal Timestamps",
        f"- **Total**: {result['unique_signal_timestamps_total']}",
    ])
    uts_gap = result['unique_signal_timestamps_in_gap']
    uts_ratio = result['unique_signal_timestamps_gap_ratio']
    lines.append(f"- **In Gap**: {uts_gap} ({uts_ratio:.2%})")
    lines.extend([
        "",
        "### Trade Candidates (Estimated)",
        f"- **Total**: {result.get('trade_candidates_total')}",
    ])
    tc_gap = result.get('trade_candidates_in_gap')
    tc_ratio = result.get('trade_candidates_gap_ratio', 0) or 0
    if tc_gap == 0:
        tc_ratio = 0.0
        result['trade_candidates_gap_ratio'] = 0.0
    lines.append(f"- **In Gap**: {tc_gap} ({tc_ratio:.2%})")
    lines.extend([
        "",
        f"- **Largest Gap**: {result['largest_gap_duration']}",
        f"- **Biased by Missing Segment**: {result['is_biased_by_missing_segment']}",
    ])
    
    write_research_report(
        name=report_name,
        payload=result,
        title=f"Intrabar Gap Impact Analysis - {args.version}",
        lines=lines,
        output_dir="reports/research"
    )
    
    print(f"Report generated: reports/research/{report_name}.md")


if __name__ == "__main__":
    main()
