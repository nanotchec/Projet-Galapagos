from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from datetime import UTC, datetime

import pandas as pd
import numpy as np

try:
    from _bootstrap import bootstrap_src_path
    bootstrap_src_path()
except ImportError:
    pass

from galapagos.research.signal_selection.loader import load_selection_inputs, reconstruct_policy_results
from galapagos.research.signal_selection.selection_rules import apply_signal_filter
from galapagos.research.signal_selection.temporal_splits import get_temporal_splits
from galapagos.research.signal_selection.same_frequency_random import analyze_frequency_preserving_random
from galapagos.research.signal_selection.cost_sensitivity import analyze_cost_sensitivity
from galapagos.research.signal_selection.placebo_tests import run_placebo_tests
from galapagos.research.signal_selection.stability_analysis import analyze_stability
from galapagos.research.signal_selection.overfit_audit import audit_overfit
from galapagos.research.signal_selection.report_models import save_signal_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="V1.25 Robust Signal Selection Validation")
    parser.add_argument("--predictions", default="data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_3.parquet")
    parser.add_argument("--dataset", default="data/gold/research_dataset/BTC/4h/research_dataset_with_alpha_scores.parquet")
    parser.add_argument("--intrabar", default="data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_22.parquet")
    parser.add_argument("--trade-ledger-report", default="reports/research/trade_ledger_intrabar_eval_v1_22_1.json")
    parser.add_argument("--features-report", required=True)
    parser.add_argument("--filter-sweep-report", required=True)
    parser.add_argument("--random-report", required=True)
    parser.add_argument("--walk-forward-report", required=True)
    parser.add_argument("--version", default="v1.25")
    
    args = parser.parse_args()
    v_v = args.version.replace(".", "_")
    
    print(f"--- Galapagos {args.version} Robust Signal Selection Validation ---")
    
    # 1. Load context
    print("Loading data...")
    signals_df, dataset, intrabar, status = load_selection_inputs(
        predictions_path=args.predictions,
        dataset_path=args.dataset,
        intrabar_path=args.intrabar
    )
    
    if status["status"] != "loaded":
        print(f"Error loading inputs: {status}")
        return

    # 2. Reconstruct Evaluation for best policy
    print("Reconstructing evaluation (memory-only)...")
    policy_name = "horizon_only"
    reconstructed = reconstruct_policy_results(
        signals_df=signals_df,
        dataset=dataset,
        intrabar=intrabar,
        policies=[policy_name]
    )
    
    bundle = reconstructed[policy_name]
    # Reconstruct DF from Pydantic models
    candidates_list = [c.model_dump() for c in bundle["candidates"]]
    results_list = [r.model_dump() for r in bundle["results"]]
    
    candidates_df = pd.DataFrame(candidates_list)
    results_df = pd.DataFrame(results_list)
    
    if not results_df.empty and not candidates_df.empty:
        full_pool_df = candidates_df.merge(results_df, on="candidate_id", how="inner", suffixes=("", "_res"))
        # Standardize columns
        if "pnl_pct" in full_pool_df:
            full_pool_df["gross_pnl_pct"] = full_pool_df["pnl_pct"]
        if "pnl_after_cost_pct" in full_pool_df:
            full_pool_df["net_pnl_pct"] = full_pool_df["pnl_after_cost_pct"]
        if "cost_proxy_pct" in full_pool_df:
            full_pool_df["cost_pct"] = full_pool_df["cost_proxy_pct"]
            
        full_pool_df["timestamp"] = pd.to_datetime(full_pool_df["signal_time"])
        if "predicted_probability" not in full_pool_df and "signal_score" in full_pool_df:
            full_pool_df["predicted_probability"] = full_pool_df["signal_score"]
    else:
        print("Error: Reconstructed evaluation is empty.")
        return
    
    # 3. Apply Target Filter
    filter_name = "low_frequency_strict_score"
    print(f"Applying filter: {filter_name}")
    filtered_indices = apply_signal_filter(full_pool_df, filter_name)
    filtered_df = full_pool_df.loc[filtered_indices].copy()
    
    if filtered_df.empty:
        print("Error: Filtered trades set is empty. Check filter logic.")
        return

    # 4. Temporal Robustness
    print("Running Temporal Robustness analysis...")
    splits = get_temporal_splits(filtered_df)
    temporal_results = {}
    for name, split_df in splits.items():
        temporal_results[name] = {
            "count": len(split_df),
            "mean_pnl": float(split_df["net_pnl_pct"].mean()),
            "total_pnl": float(split_df["net_pnl_pct"].sum()),
            "win_rate": float((split_df["net_pnl_pct"] > 0).mean())
        }
    save_signal_report(f"signal_selection_temporal_robustness_{v_v}", temporal_results)

    # 5. Same Frequency Random
    print("Running Same-Frequency Random analysis...")
    sf_random = analyze_frequency_preserving_random(full_pool_df, filtered_df)
    save_signal_report(f"signal_selection_same_frequency_random_{v_v}", sf_random)

    # 6. Cost Sensitivity
    print("Running Cost Sensitivity analysis...")
    cost_sens = analyze_cost_sensitivity(filtered_df)
    save_signal_report(f"signal_selection_cost_sensitivity_{v_v}", cost_sens)

    # 7. Placebo Tests
    print("Running Placebo tests...")
    placebo = run_placebo_tests(full_pool_df, filtered_indices)
    save_signal_report(f"signal_selection_placebo_tests_{v_v}", placebo)

    # 8. Stability Analysis
    print("Running Stability analysis...")
    stability = analyze_stability(filtered_df)
    save_signal_report(f"signal_selection_stability_{v_v}", stability)

    # 9. Overfit Audit
    print("Running Overfit Audit...")
    with open(args.filter_sweep_report) as f:
        sweep = json.load(f)
    rows = sweep.get("rows", sweep.get("sweep_results", []))
    rules_tested = len(rows)
    # Use the new BEATS_MONTHLY_COUNT_RANDOM verdict
    beats_monthly_random = sf_random["verdict"] == "BEATS_MONTHLY_COUNT_RANDOM"
    overfit = audit_overfit(rules_tested, beats_monthly_random)
    save_signal_report(f"signal_selection_overfit_audit_{v_v}", overfit)

    # 10. Synthesis
    print("Synthesizing final V1.25.1 results...")
    
    robustness_blockers = []
    if overfit["verdict"] == "MULTIPLE_TESTING_RISK_HIGH":
        robustness_blockers.append("MULTIPLE_TESTING_RISK_HIGH")
    if stability["verdict"] == "PERFORMANCE_CONCENTRATED":
        robustness_blockers.append("PERFORMANCE_CONCENTRATED")
    
    recent_2026 = temporal_results.get("2026", {})
    recent_count = recent_2026.get("count", 0)
    recent_mean = recent_2026.get("mean_pnl", 0)
    
    if recent_count < 20:
        robustness_blockers.append("RECENT_SAMPLE_TOO_SMALL")
    if recent_mean <= 0:
        robustness_blockers.append("RECENT_WINDOW_NEGATIVE_OR_WEAK")

    final_verdict = "PROMISING_BUT_NOT_ROBUST_RECENT_WEAK"
    if robustness_blockers:
        final_verdict = "PROMISING_BUT_REQUIRES_OUT_OF_SAMPLE_CONFIRMATION"
    
    summary = {
        "version": args.version,
        "candidate_filter": filter_name,
        "temporal_robustness": temporal_results,
        "sf_random": sf_random,
        "cost_sensitivity": cost_sens,
        "placebo": placebo,
        "stability": stability,
        "overfit": overfit,
        "robustness_blockers": robustness_blockers,
        "multiple_testing_warning": overfit["multiple_testing_warning"],
        "performance_concentration_warning": stability.get("performance_concentration_warning", False),
        "recent_window_warning": recent_count < 20 or recent_mean <= 0,
        "final_verdict": final_verdict,
        "ready_for_reviewer": False,
        "methodology_honesty": {
            "random_baseline": "monthly_count_preserving_random",
            "placebo_status": "PLACEBO_PARTIAL",
            "cost_audit": cost_sens["cost_reconstruction_status"]
        }
    }
    
    save_signal_report(f"signal_selection_robust_validation_summary_{v_v}", summary)
    
    # Recommendation
    reco = {
        "version": args.version,
        "primary_recommendation": "Maintain filter as research hypothesis; do not promote to production.",
        "recommended_next_step": "Pre-registered validation protocol on future data.",
        "do_not_do_next": ["ACTIVATE_REVIEWER", "EXECUTE_HOLDOUT", "REAL_TRADING"],
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True
    }
    save_signal_report("v1_25_1_recommendation", reco)
    
    print(f"--- Galapagos {args.version} Complete ---")

if __name__ == "__main__":
    main()
