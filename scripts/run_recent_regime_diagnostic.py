from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.recent_regime_diagnostic.data_loader import load_diagnostic_data, separate_frames
from galapagos.research.recent_regime_diagnostic.selected_filter_rebuilder import rebuild_selected_filter_consistent
from galapagos.research.recent_regime_diagnostic.recent_window_diagnostic import run_recent_window_diagnostic
from galapagos.research.recent_regime_diagnostic.regime_dependency import run_regime_dependency_diagnostic
from galapagos.research.recent_regime_diagnostic.calibration_drift import run_calibration_drift_diagnostic
from galapagos.research.recent_regime_diagnostic.score_distribution_drift import run_score_distribution_drift
from galapagos.research.recent_regime_diagnostic.cost_drag_diagnostic import run_cost_drag_diagnostic
from galapagos.research.recent_regime_diagnostic.outcome_distribution import run_outcome_distribution_diagnostic
from galapagos.research.recent_regime_diagnostic.regime_definition_audit import run_regime_definition_audit
from galapagos.research.recent_regime_diagnostic.recommendation_engine import generate_diagnostic_recommendation
from galapagos.research.causal_signal_research.report_writer import save_research_report

def main():
    parser = argparse.ArgumentParser(description="Run Recent/Regime Diagnostic (V1.29.5)")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset")
    parser.add_argument("--intrabar")
    parser.add_argument("--causal-summary")
    parser.add_argument("--version", default="v1.29.5")
    args = parser.parse_args()

    print(f"--- Galapagos {args.version} Recent/Regime Diagnostic ---")
    v_norm = args.version.lower().replace(".", "_")

    # 1. Load data
    df_raw = load_diagnostic_data(args.predictions)
    selection_frame, outcome_frame = separate_frames(df_raw)
    
    # 2. Rebuild filter CONSISTENTLY (including dedup)
    threshold = 0.65
    mask, audit = rebuild_selected_filter_consistent(df_raw, threshold)
    save_research_report(f"recent_regime_selected_filter_rebuild_{v_norm}", audit)
    
    if audit["rebuild_status"] == "REBUILD_MISMATCH_DETECTION":
        print(f"WARNING: Selected count mismatch! Expected 225, got {audit['selected_count_final']}")
        # We continue but the consistency check will catch it later
    
    # 3. Run Diagnostics on de-duplicated selected trades
    # We must merge to get outcomes for diagnostics
    diagnostics = {}
    
    # Definition audit first to pass status to dependency
    def_audit = run_regime_definition_audit(selection_frame)
    diagnostics["regime_definition_audit"] = def_audit
    
    diagnostics["recent_window_diagnostic"] = run_recent_window_diagnostic(mask, selection_frame, outcome_frame)
    diagnostics["regime_dependency_diagnostic"] = run_regime_dependency_diagnostic(
        mask, selection_frame, outcome_frame, 
        regime_definition_status=def_audit["regime_definition_status"]
    )
    diagnostics["calibration_drift_diagnostic"] = run_calibration_drift_diagnostic(mask, selection_frame, outcome_frame)
    diagnostics["score_distribution_drift"] = run_score_distribution_drift(selection_frame)
    diagnostics["cost_drag_diagnostic"] = run_cost_drag_diagnostic(mask, selection_frame, outcome_frame)
    diagnostics["outcome_distribution_diagnostic"] = run_outcome_distribution_diagnostic(mask, selection_frame, outcome_frame)
    
    # Save individual reports with standard names
    for key, data in diagnostics.items():
        save_research_report(f"{key}_{v_norm}", data)
        
    # 4. Synthesize Recommendation
    reco = generate_diagnostic_recommendation(diagnostics)
    save_research_report(f"{v_norm}_recommendation", reco)
    
    # Summary
    summary = {
        "version": args.version,
        "selection_leakage_status": "CLEAN" if not audit["forbidden_columns_found"] else "LEAKAGE_DETECTED",
        "forbidden_columns_found": audit["forbidden_columns_found"],
        "selected_count_final": audit["selected_count_final"],
        "selected_count_matches_v1_29_3": audit["selected_count_matches_v1_29_3"],
        "rebuild_status": audit["rebuild_status"],
        "recent_degradation_confirmed": diagnostics["recent_window_diagnostic"]["recent_degradation_confirmed"],
        "recent_window_net_mean_pnl": diagnostics["recent_window_diagnostic"]["recent_net_mean_pnl"],
        "regime_dependency_status": diagnostics["regime_dependency_diagnostic"]["regime_dependency_status"],
        "regime_definition_status": def_audit["regime_definition_status"],
        "cost_drag_status": diagnostics["cost_drag_diagnostic"]["cost_drag_status"],
        "score_distribution_status": diagnostics["score_distribution_drift"]["score_distribution_status"],
        "final_diagnostic_verdict": reco["final_diagnostic_verdict"] if audit["rebuild_status"] == "REBUILD_COMPLETE_NO_SELECTION_LEAKAGE" else "DIAGNOSTIC_BLOCKED_SELECTION_LEAKAGE",
        "do_not_progress_to_v1_30": True,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True
    }
    save_research_report(f"recent_regime_diagnostic_summary_{v_norm}", summary)
    
    print(f"--- Diagnostic Complete: {summary['final_diagnostic_verdict']} ---")

if __name__ == "__main__":
    main()
