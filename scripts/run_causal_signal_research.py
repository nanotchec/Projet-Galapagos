from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.causal_signal_research.threshold_grid import build_causal_research_grid
from galapagos.research.causal_signal_research.causal_safety_audit import audit_filter_causality
from galapagos.research.causal_signal_research.causal_filter_evaluator import evaluate_filter_performance
from galapagos.research.causal_signal_research.overfit_guard import calculate_overfit_risk
from galapagos.research.causal_signal_research.report_writer import save_research_report
from galapagos.research.causal_signal_research.signal_dedup_audit import audit_signal_dedup, apply_dedup_policy
from galapagos.research.causal_signal_research.same_count_random import run_random_baselines, run_monthly_random_baselines
from galapagos.research.causal_signal_research.temporal_robustness import analyze_temporal_robustness
from galapagos.research.causal_signal_research.regime_breakdown import analyze_regime_breakdown

def main():
    parser = argparse.ArgumentParser(description="Run Causal Signal Research (V1.29.3)")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset")
    parser.add_argument("--intrabar")
    parser.add_argument("--trade-ledger-report")
    parser.add_argument("--version", default="v1.29.3")
    parser.add_argument("--dedup-policy", default="first_stable_per_timestamp")
    args = parser.parse_args()

    print(f"--- Galapagos {args.version} Causal Signal Research ---")
    v_norm = args.version.lower().replace(".", "_")

    # 1. Load data
    try:
        preds = pd.read_parquet(args.predictions)
        if "timestamp" in preds.columns:
            preds["timestamp"] = pd.to_datetime(preds["timestamp"], utc=True)
    except Exception as e:
        print(f"Error loading predictions: {e}")
        preds = pd.DataFrame()

    if preds.empty:
        print("Predictions dataframe is empty. Aborting.")
        sys.exit(1)

    # 2. Data Separation
    forbidden_cols = [
        "forward_return_6bar", "forward_return_12bar", "cost_adjusted_forward_return",
        "net_pnl_pct", "gross_pnl_pct", "mfe_pct", "mae_pct", "exit_reason", "simulation_status"
    ]
    
    selection_cols = [c for c in preds.columns if c not in forbidden_cols]
    outcome_cols = [c for c in preds.columns if c in forbidden_cols or c == "timestamp"]
    
    selection_frame_raw = preds[selection_cols].copy()
    outcome_frame_raw = preds[outcome_cols].copy()
    
    # 3. Dedup Robustness
    dedup_audit = audit_signal_dedup(selection_frame_raw)
    save_research_report(f"causal_signal_dedup_robustness_{v_norm}", dedup_audit)
    
    selection_frame = apply_dedup_policy(selection_frame_raw, policy=args.dedup_policy)
    outcome_frame = outcome_frame_raw.loc[selection_frame.index]

    # 4. Grid
    grid = build_causal_research_grid()
    
    audit_reports = []
    eval_reports = []
    random_reports = []
    temporal_reports = []
    regime_reports = []
    
    for filter_obj in grid:
        audit = audit_filter_causality(filter_obj)
        audit_reports.append(audit)
        
        mask = filter_obj.apply(selection_frame)
        perf = evaluate_filter_performance(mask, selection_frame, outcome_frame)
        perf["filter_name"] = filter_obj.get_metadata().name
        eval_reports.append(perf)
        
        if audit["causal_status"] == "CAUSAL_FILTER_PASSED":
            pnl_col = "forward_return_12bar"
            if "net_pnl_pct" in outcome_frame.columns:
                 pnl_col = "net_pnl_pct"
            
            if perf.get("selected_count", 0) > 0:
                selected_indices = mask[mask].index
                
                # Random Baselines
                global_rand = run_random_baselines(perf["selected_count"], perf["net_mean_pnl"], outcome_frame[pnl_col])
                monthly_rand = run_monthly_random_baselines(selected_indices, selection_frame, outcome_frame, pnl_col)
                
                res_rand = {**global_rand}
                if monthly_rand.get("status") == "MONTHLY_RANDOM_BASELINE_COMPLETE":
                    res_rand.update({
                        "monthly_random_p95": monthly_rand["monthly_random_p95"],
                        "beats_monthly_random_p95": monthly_rand["beats_monthly_random_p95"],
                        "approximate_p_value_monthly": monthly_rand["approximate_p_value_monthly"]
                    })
                res_rand["filter_name"] = perf["filter_name"]
                random_reports.append(res_rand)
                
                # Temporal
                temporal = analyze_temporal_robustness(mask, selection_frame, outcome_frame, pnl_col)
                temporal["filter_name"] = perf["filter_name"]
                temporal_reports.append(temporal)
                
                # Regime
                regime = analyze_regime_breakdown(mask, selection_frame, outcome_frame, pnl_col)
                regime["filter_name"] = perf["filter_name"]
                regime_reports.append(regime)

    # Save reports
    save_research_report(f"causal_filter_safety_audit_{v_norm}", {"filters": audit_reports})
    save_research_report(f"causal_filter_evaluation_{v_norm}", {"evaluations": eval_reports})
    save_research_report(f"causal_filter_random_baselines_{v_norm}", {"baselines": random_reports})
    save_research_report(f"causal_filter_temporal_robustness_{v_norm}", {"temporal": temporal_reports})
    save_research_report(f"causal_filter_regime_breakdown_{v_norm}", {"regimes": regime_reports})
    
    # 5. Summary
    best_filter = None
    best_pnl = -float('inf')
    
    passed_names = [a["filter_name"] for a in audit_reports if a["causal_status"] == "CAUSAL_FILTER_PASSED"]
    
    for e in eval_reports:
        if e["filter_name"] in passed_names and e.get("selected_count", 0) >= 60:
            rand = next((r for r in random_reports if r["filter_name"] == e["filter_name"]), None)
            temp = next((t for t in temporal_reports if t["filter_name"] == e["filter_name"]), None)
            reg = next((rg for rg in regime_reports if rg["filter_name"] == e["filter_name"]), None)
            
            if rand and rand.get("beats_monthly_random_p95", False):
                # Stricter checks for promising
                if temp and temp["status"] == "TEMPORAL_ROBUSTNESS_PROMISING":
                    if reg and reg["status"] == "REGIME_BREAKDOWN_COMPLETE":
                        if e["net_mean_pnl"] > best_pnl:
                            best_pnl = e["net_mean_pnl"]
                            best_filter = e["filter_name"]
                            
    # Final Verdict Logic
    final_verdict = "NO_CAUSAL_FILTER_PROMISING"
    if best_filter:
        final_verdict = "CAUSAL_FILTER_PROMISING_BUT_REQUIRES_PREREGISTRATION"
    else:
        # Check why it's not promising
        top_filter_raw = max(eval_reports, key=lambda x: x.get("net_mean_pnl", -999) if x["filter_name"] in passed_names else -1000)
        top_name = top_filter_raw["filter_name"]
        
        temp_top = next((t for t in temporal_reports if t["filter_name"] == top_name), None)
        reg_top = next((rg for rg in regime_reports if rg["filter_name"] == top_name), None)
        rand_top = next((r for r in random_reports if r["filter_name"] == top_name), None)
        
        if temp_top and temp_top["status"] == "TEMPORAL_ROBUSTNESS_RECENT_WEAK":
            final_verdict = "CAUSAL_FILTER_EXPLORATORY_RECENT_WINDOW_WEAK"
        elif reg_top and reg_top["status"] == "REGIME_BREAKDOWN_SINGLE_REGIME_DOMINANT":
            final_verdict = "CAUSAL_FILTER_EXPLORATORY_REGIME_DEPENDENT"
        elif rand_top and not rand_top.get("beats_monthly_random_p95", False):
            final_verdict = "CAUSAL_FILTER_EXPLORATORY_FAILED_MONTHLY_BASELINE"
            
    summary = {
        "version": args.version,
        "causal_filters_tested": len(grid),
        "causal_filters_passed_audit": len(passed_names),
        "data_separation_status": "DATA_SEPARATION_PASSED",
        "dedup_robustness_status": dedup_audit["dedup_robustness_status"],
        "best_filter_observed": best_filter if best_filter else top_name,
        "best_filter_net_mean_pnl": best_pnl if best_filter else top_filter_raw.get("net_mean_pnl"),
        "final_verdict": final_verdict,
        "evidence_classification": "EXPLORATORY_ONLY",
        "recommended_next_step": "V1.30 preregister new causal filter protocol" if final_verdict == "CAUSAL_FILTER_PROMISING_BUT_REQUIRES_PREREGISTRATION" else "fix robustness issues / improve alpha"
    }
    save_research_report(f"causal_signal_research_summary_{v_norm}", summary)
    
    reco = {
        "final_verdict": final_verdict,
        "recommended_next_step": summary["recommended_next_step"],
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True
    }
    save_research_report(f"{v_norm}_recommendation", reco)
    print(f"--- Research Complete: {final_verdict} ---")

if __name__ == "__main__":
    main()
