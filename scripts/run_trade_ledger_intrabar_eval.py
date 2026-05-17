from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from _bootstrap import bootstrap_src_path
    bootstrap_src_path()
except ImportError:
    pass

from galapagos.research.trade_ledger.comparison import compare_policies
from galapagos.research.trade_ledger.intrabar_evaluator import evaluate_trade_candidates_intrabar
from galapagos.research.trade_ledger.ledger_builder import build_trade_candidates
from galapagos.research.trade_ledger.metrics import calculate_policy_metrics
from galapagos.research.trade_ledger.signal_loader import load_ml_signals


def main():
    """Main execution flow for V1.19 evaluation."""
    parser = argparse.ArgumentParser(description="V1.19 Trade Ledger Evaluator")
    parser.add_argument("--predictions", help="Path to ML predictions parquet")
    parser.add_argument("--dataset", help="Path to 4h research dataset parquet")
    parser.add_argument("--intrabar", help="Path to 5m intrabar sample parquet")
    parser.add_argument(
        "--policies",
        default="fixed_percent,atr_proxy,horizon_only",
        help="Comma separated policies",
    )
    parser.add_argument("--version", default="v1.19", help="Version tag")
    parser.add_argument("--dry-run", action="store_true", help="Only load and audit signals")

    args = parser.parse_args()

    print(f"--- Galapagos {args.version} Orchestrator ---")

    # 1. Load and Audit Signals
    print("Loading signals...")
    try:
        signals_df, audit_signals = load_ml_signals(args.predictions or "missing.parquet")
    except Exception as e:
        print(f"Warning: Signal loading failed: {e}")
        signals_df, audit_signals = pd.DataFrame(), {"status": "failed"}

    if args.dry_run:
        print(f"Dry-run: {len(signals_df)} unique signals ready for evaluation.")
        print(f"Audit: {audit_signals}")
        print("Dry-run complete.")
        return

    if signals_df.empty:
        print("Error: No signals loaded. Check predictions path.")
        return

    # 2. Load context data
    print("Loading 4h dataset and intrabar data...")
    if not Path(args.dataset).exists():
        print(f"Error: Dataset {args.dataset} not found.")
        return
    if not Path(args.intrabar).exists():
        print(f"Error: Intrabar sample {args.intrabar} not found.")
        return

    ohlcv_4h = pd.read_parquet(args.dataset)
    intrabar_df = pd.read_parquet(args.intrabar)

    policy_names = args.policies.split(",")
    all_metrics = {}
    ledger_audit = {}
    eval_audit = {}

    for p_name in policy_names:
        print(f"Evaluating policy: {p_name}...")

        # 3. Build Candidates
        candidates = build_trade_candidates(signals_df, ohlcv_4h, p_name)
        print(f"  - Built {len(candidates)} candidates.")

        p_ledger_audit = {
            "candidates_count": len(candidates),
            "fallback_entry_count": sum(
                1 for c in candidates if c.data_availability.get("fallback_entry")
            ),
            "next_candle_entry_count": sum(
                1 for c in candidates if not c.data_availability.get("fallback_entry")
            ),
        }
        ledger_audit[p_name] = p_ledger_audit

        # 4. Evaluate Intrabar
        results = evaluate_trade_candidates_intrabar(candidates, intrabar_df)

        # 5. Compute Metrics and Audit
        metrics = calculate_policy_metrics(results)
        all_metrics[p_name] = metrics

        p_eval_audit = {
            "evaluated_count": metrics.get("evaluated_count", 0),
            "missing_intrabar_count": sum(
                1 for r in results if r.simulation_status == "missing_data"
            ),
            "coverage_mean": (
                pd.Series([r.coverage_pct for r in results]).mean() if results else 0.0
            ),
            "ambiguous_rate": metrics.get("ambiguous_rate", 0.0),
        }
        eval_audit[p_name] = p_eval_audit

        print(f"  - Evaluated {metrics.get('evaluated_count')} candidates.")
        print(f"  - Win Rate: {metrics.get('win_rate', 0.0):.2%}")

    # 6. Final Comparison and Verdict
    print("Comparing policies...")
    comparison = compare_policies(all_metrics)
    print(f"Verdict: {comparison.get('verdict')}")

    # 7. Generate Reports
    print("Generating reports...")
    from galapagos.research.trade_ledger.report import (
        generate_v1_20_1_reports,
        generate_v1_21_1_reports,
        generate_v1_21_2_reports,
        generate_v1_21_5_reports,
        generate_v1_21_reports,
        generate_v1_22_1_reports,
        generate_v1_22_reports,
    )

    intrabar_meta = {
        "file_path": str(Path(args.intrabar).resolve()),
        "rows": len(intrabar_df),
        "first_timestamp": str(intrabar_df["timestamp"].min()),
        "last_timestamp": str(intrabar_df["timestamp"].max()),
        "inferred_days": (
            intrabar_df["timestamp"].max() - intrabar_df["timestamp"].min()
        ).total_seconds() / 86400
    }
    
    # Try to load gap analysis if it exists
    v_norm = args.version.replace(".", "_")
    gap_impact_path = Path("reports/research") / f"intrabar_gap_impact_{v_norm}.json"
    gap_analysis = None
    if gap_impact_path.exists():
        with open(gap_impact_path) as f:
            gap_analysis = json.load(f)

    if args.version == "v1.22.1":
        generate_v1_22_1_reports(
            all_metrics,
            comparison,
            audit_signals,
            ledger_audit,
            eval_audit,
            version=args.version,
            intrabar_metadata=intrabar_meta,
            gap_analysis=gap_analysis
        )
    elif args.version == "v1.22":
        generate_v1_22_reports(
            all_metrics,
            comparison,
            audit_signals,
            ledger_audit,
            eval_audit,
            version=args.version,
            intrabar_metadata=intrabar_meta,
            gap_analysis=gap_analysis
        )
    elif args.version == "v1.21.5":
        generate_v1_21_5_reports(
            all_metrics,
            comparison,
            audit_signals,
            ledger_audit,
            eval_audit,
            version=args.version,
            intrabar_metadata=intrabar_meta,
            gap_analysis=gap_analysis
        )
    elif args.version == "v1.21.2":
        generate_v1_21_2_reports(
            all_metrics,
            comparison,
            audit_signals,
            ledger_audit,
            eval_audit,
            version=args.version,
            intrabar_metadata=intrabar_meta,
            gap_analysis=gap_analysis
        )
    elif args.version == "v1.21.1":
        generate_v1_21_1_reports(
            all_metrics,
            comparison,
            audit_signals,
            ledger_audit,
            eval_audit,
            version=args.version,
            intrabar_metadata=intrabar_meta,
            gap_analysis=gap_analysis
        )
    elif args.version == "v1.21":
        generate_v1_21_reports(
            all_metrics,
            comparison,
            audit_signals,
            ledger_audit,
            eval_audit,
            version=args.version,
            intrabar_metadata=intrabar_meta
        )
    else:
        generate_v1_20_1_reports(
            all_metrics, 
            comparison, 
            audit_signals, 
            ledger_audit, 
            eval_audit, 
            version=args.version,
            intrabar_metadata=intrabar_meta
        )

    print(f"--- Orchestration {args.version} Complete ---")


if __name__ == "__main__":
    main()
