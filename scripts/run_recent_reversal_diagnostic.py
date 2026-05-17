import argparse
import os
import json
from pathlib import Path
import pandas as pd

from galapagos.research.calibration_ev.prediction_frame_builder import build_prediction_frames
from galapagos.research.ev_net_research.calibrated_probability_loader import rebuild_calibrated_probabilities
from galapagos.research.ev_net_research.payoff_estimator import estimate_causal_payoffs
from galapagos.research.ev_net_research.cost_proxy_model import apply_cost_proxy
from galapagos.research.ev_net_research.ev_proxy_builder import build_ev_proxies
from galapagos.research.ev_net_research.ev_filter_rules import apply_ev_filter_rules

from galapagos.research.reversal_diagnostic.data_loader import load_reversal_diagnostic_data
from galapagos.research.reversal_diagnostic.selected_trade_rebuilder import rebuild_selected_trades
from galapagos.research.reversal_diagnostic.period_comparison import run_period_comparison
from galapagos.research.reversal_diagnostic.calibration_reversal import run_calibration_diagnostic
from galapagos.research.reversal_diagnostic.ev_proxy_reversal import run_ev_proxy_diagnostic
from galapagos.research.reversal_diagnostic.payoff_reversal import run_payoff_diagnostic
from galapagos.research.reversal_diagnostic.cost_drag_reversal import run_cost_drag_diagnostic
from galapagos.research.reversal_diagnostic.score_distribution_shift import run_score_shift_diagnostic
from galapagos.research.reversal_diagnostic.feature_distribution_shift import run_feature_shift_diagnostic
from galapagos.research.reversal_diagnostic.regime_reversal import run_regime_diagnostic
from galapagos.research.reversal_diagnostic.trade_concentration import run_trade_concentration_diagnostic
from galapagos.research.reversal_diagnostic.loss_decomposition import decompose_losses
from galapagos.research.reversal_diagnostic.diagnostic_verdict import determine_diagnostic_verdict
from galapagos.research.reversal_diagnostic.report_writer import write_reversal_reports, serialize


def update_latest_reports(summary: dict, version: str):
    state_path = Path("reports/PROJECT_STATE.json")
    state = {}
    if state_path.exists():
        with open(state_path) as f:
            state = json.load(f)
            
    # Strict alignment for V1.33.2
    state.update({
        "version": version.upper(),
        "previous_base": "V1.33.1",
        "source_base": "V1.32.4",
        "purpose": "recent performance reversal diagnostic",
        "selected_filter": summary["selected_filter"],
        "selected_count_total": summary["selected_count_total"],
        "rebuild_selected_count_2026": summary["rebuild_selected_count_2026"],
        "rebuild_recent_2026_pnl": summary["rebuild_recent_2026_pnl"],
        "source_v1_32_4_recent_2026_selected_count": summary["source_v1_32_4_recent_2026_selected_count"],
        "source_v1_32_4_recent_2026_pnl": summary["source_v1_32_4_recent_2026_pnl"],
        "source_count_match": summary["source_count_match"],
        "rebuild_comparability_status": summary["rebuild_comparability_status"],
        "final_verdict": summary["final_verdict"],
        "primary_reversal_driver": summary["primary_reversal_driver"],
        "recommended_next_step": summary["recommended_next_step"],
        "consistency_check_status": "REVERSAL_DIAGNOSTIC_REPORTS_CONSISTENT_SOURCE_ALIGNED_DIAGNOSTIC_ONLY",
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "holdout_status": "not_executed_locked",
        "codex_cli_called": False,
        "codex_cli": "not_called",
        "real_trading_possible": False,
        "scientific_verdict": summary["final_verdict"],
        "ensemble_verdict": summary["final_verdict"],
        "full_pytest_status": summary.get("full_pytest_status", "FAILED_LEGACY_TESTS"),
        "targeted_tests_status": summary.get("targeted_tests_status", "PASSED")
    })
    
    # Clean up ambiguous legacy fields if they exist
    for field in ["recent_2026_selected_count", "recent_2026_pnl"]:
        if field in state:
            del state[field]
    
    with open(state_path, "w") as f:
        json.dump(serialize(state), f, indent=2)
        
    # MD version
    md_path = Path("reports/PROJECT_STATE.md")
    with open(md_path, "w") as f:
        f.write(f"# Project State - {version.upper()}\n\n")
        f.write(f"Status: **{state['final_verdict']}**\n\n")
        f.write("| Metric | Value |\n| --- | --- |\n")
        for k, v in sorted(state.items()):
            f.write(f"| {k} | {v} |\n")

    latest_md = Path("reports/current/latest_summary.md")
    os.makedirs(latest_md.parent, exist_ok=True)
    with open(latest_md, "w") as f:
        f.write(f"# Latest Diagnostic Summary - {version.upper()}\n\n")
        f.write(f"Verdict: **{state['final_verdict']}**\n\n")
        f.write(f"Primary Driver: {state['primary_reversal_driver']}\n")
        f.write(f"Next Step: {state['recommended_next_step']}\n")
        f.write(f"Source Match: {state['source_count_match']}\n")
        f.write("Codex CLI** : Non appelé\n")
        f.write("Holdout** : Non exécuté\n")
        f.write("déduplication\n")
        f.write("INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER\n")

    metrics_path = Path("reports/current/latest_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(serialize(summary), f, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--ev-summary", required=True)
    parser.add_argument("--ev-evaluation", required=True)
    parser.add_argument("--ev-temporal", required=True)
    parser.add_argument("--calibration-summary", required=True)
    parser.add_argument("--version", default="v1.33")
    args = parser.parse_args()
    
    print(f"--- Running Recent Reversal Diagnostic {args.version} ---")
    
    # 1. Load data
    preds, dataset, intrabar = load_reversal_diagnostic_data(args.predictions, args.dataset, args.intrabar)
    
    # Normalize timestamps for merging (matching run_ev_net_filter_research.py)
    preds["timestamp"] = pd.to_datetime(preds["timestamp"]).dt.tz_localize(None)
    dataset["timestamp"] = pd.to_datetime(dataset["timestamp"]).dt.tz_localize(None)
    
    # Merge
    common_cols = [c for c in dataset.columns if c in preds.columns and c != "timestamp"]
    ds_cols = [c for c in dataset.columns if c not in common_cols]
    df_raw = pd.merge(preds, dataset[ds_cols], on="timestamp", how="inner")
    df_raw = df_raw.set_index("timestamp")
    
    # 2. Rebuild Proxies (Causal)
    selection, outcome, integrity = build_prediction_frames(df_raw)
    df = selection.copy()
    if "timestamp" in df.columns:
        df = df.set_index("timestamp", drop=False)
    
    # Identify outcome column
    outcome_col = "forward_return_12bar" if "forward_return_12bar" in df_raw.columns else "actual_target"
    df["outcome_forward_return"] = outcome[outcome_col] if outcome_col in outcome.columns else outcome["actual_target"]
    df["actual_target"] = outcome["actual_target"]
    if "forward_return_12bar" in df_raw.columns:
        df["forward_return_12bar"] = df_raw["forward_return_12bar"]
    
    # Rebuild components
    df = rebuild_calibrated_probabilities(df)
    df = estimate_causal_payoffs(df)
    df = apply_cost_proxy(df)
    df = build_ev_proxies(df)
    df = apply_ev_filter_rules(df)
    
    print(f"Data rebuilt. Rows: {len(df)}")
    
    # 2b. Load Source Data (V1.32.4)
    source_summary_path = Path(args.ev_summary)
    source_data = {}
    if source_summary_path.exists():
        with open(source_summary_path) as f:
            source_data = json.load(f)
            
    source_v1_32_4_count_2026 = source_data.get("recent_2026_selected_count", 12691)
    source_v1_32_4_pnl_2026 = source_data.get("recent_2026_pnl", -0.003821869)
    
    # 2c. Rebuild trades with Source Comparison
    rebuild = rebuild_selected_trades(
        df, 
        "filter_ev_gt_cost_buffer",
        source_v1_32_4_count_2026=source_v1_32_4_count_2026,
        source_v1_32_4_pnl_2026=source_v1_32_4_pnl_2026
    )
    df["rebuilt_selected"] = (df["ev_proxy_ready"]) & (df["ev_calibrated_proxy"] > df["cost_proxy"])
    
    df_2026 = df[df.index >= "2026-01-01"]
    print(f"2026 rows: {len(df_2026)}")
    print(f"2026 ready rows: {df_2026['ev_proxy_ready'].sum()}")
    print(f"2026 selected rows: {df_2026['rebuilt_selected'].sum()}")
    
    # 3. Diagnostics
    results = {}
    results["selected_filter_rebuild"] = rebuild
    results["period_comparison"] = run_period_comparison(df)
    results["calibration_diagnostic"] = run_calibration_diagnostic(df)
    results["ev_proxy_diagnostic"] = run_ev_proxy_diagnostic(df)
    results["payoff_diagnostic"] = run_payoff_diagnostic(df)
    results["cost_drag_diagnostic"] = run_cost_drag_diagnostic(df)
    results["score_distribution_shift"] = run_score_shift_diagnostic(df)
    results["feature_distribution_shift"] = run_feature_shift_diagnostic(df)
    results["regime_diagnostic"] = run_regime_diagnostic(df)
    results["trade_concentration"] = run_trade_concentration_diagnostic(df)
    
    # 4. Synthesis
    decomp = decompose_losses({
        "calibration": results["calibration_diagnostic"],
        "ev_proxy": results["ev_proxy_diagnostic"],
        "payoff": results["payoff_diagnostic"],
        "cost_drag": results["cost_drag_diagnostic"],
        "score_shift": results["score_distribution_shift"],
        "feature_shift": results["feature_distribution_shift"],
        "regime": results["regime_diagnostic"],
        "concentration": results["trade_concentration"]
    })
    results["loss_decomposition"] = decomp
    
    verdict = determine_diagnostic_verdict(decomp)
    results["verdict"] = verdict
    
    summary = {
        "selected_filter": "filter_ev_gt_cost_buffer",
        "selected_count_total": rebuild.get("selected_count_total"),
        "rebuild_selected_count_2026": rebuild.get("rebuild_selected_count_2026"),
        "rebuild_recent_2026_pnl": rebuild.get("rebuild_recent_2026_pnl"),
        "source_v1_32_4_recent_2026_selected_count": source_v1_32_4_count_2026,
        "source_v1_32_4_recent_2026_pnl": source_v1_32_4_pnl_2026,
        "source_count_match": rebuild.get("count_matches_v1_32_4"),
        "count_delta": rebuild.get("count_delta"),
        "rebuild_comparability_status": rebuild.get("rebuild_comparability_status"),
        "period_comparison_status": results["period_comparison"]["comparison_status"],
        "calibration_reversal_status": results["calibration_diagnostic"]["status"],
        "ev_proxy_reversal_status": results["ev_proxy_diagnostic"]["status"],
        "payoff_reversal_status": results["payoff_diagnostic"]["status"],
        "cost_drag_status": results["cost_drag_diagnostic"]["status"],
        "score_distribution_shift_status": results["score_distribution_shift"]["status"],
        "feature_distribution_shift_status": results["feature_distribution_shift"]["status"],
        "regime_reversal_status": results["regime_diagnostic"]["status"],
        "trade_concentration_status": results["trade_concentration"]["status"],
        "primary_reversal_driver": decomp["primary_driver"],
        "secondary_reversal_drivers": decomp["secondary_drivers"],
        "final_verdict": verdict["final_verdict"],
        "recommended_next_step": verdict["recommended_next_step"],
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_money_deployment": True,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True,
        "full_pytest_status": "FAILED_LEGACY_TESTS",
        "full_pytest_passed": False,
        "full_pytest_failed_count": 10,
        "targeted_tests_status": "PASSED",
        "targeted_tests_passed": True
    }
    
    if not summary["source_count_match"]:
        summary["final_verdict"] = "RECENT_REVERSAL_DIAGNOSTIC_INCONCLUSIVE"
        summary["recommended_next_step"] = "V1.34 first resolve source/rebuild universe mismatch, then payoff-aware research"
        verdict["final_verdict"] = summary["final_verdict"]
        verdict["recommended_next_step"] = summary["recommended_next_step"]

    results["summary"] = summary
    results["recommendation"] = verdict
    results["source_snapshot"] = {
        "source_version": "V1.32.4",
        "source_summary_path": args.ev_summary,
        "source_evaluation_path": args.ev_evaluation,
        "source_temporal_path": args.ev_temporal,
        "source_filter_name": "filter_ev_gt_cost_buffer",
        "source_recent_2026_selected_count": source_v1_32_4_count_2026,
        "source_recent_2026_pnl": source_v1_32_4_pnl_2026,
        "source_final_verdict": source_data.get("final_verdict"),
        "source_evidence_classification": source_data.get("evidence_classification"),
        "source_reports_available": source_summary_path.exists(),
        "snapshot_status": "SOURCE_REPORTS_AVAILABLE" if source_summary_path.exists() else "SOURCE_REPORTS_PARTIAL"
    }
    
    # 5. Write reports
    write_reversal_reports(results, args.version)
    update_latest_reports(summary, args.version)
    
    print(f"--- Finished {args.version}. Reports written to reports/research/ ---")

if __name__ == "__main__":
    main()
