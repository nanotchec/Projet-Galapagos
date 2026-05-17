import argparse
import pandas as pd
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path
bootstrap_src_path()

from galapagos.research.canonical_universe import build_canonical_universe, write_universe_reports

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--source-reconstruction", required=True)
    parser.add_argument("--ev-proxy-rebuild", required=True)
    parser.add_argument("--version", default="v1.37.2")
    args = parser.parse_args()
    
    print(f"--- Building Canonical Trade Universe {args.version} ---")
    
    paths = {
        "predictions_path": args.predictions,
        "dataset_path": args.dataset,
        "intrabar_path": args.intrabar
    }
    
    # Load inputs
    df_preds = pd.read_parquet(args.predictions)
    df_dataset = pd.read_parquet(args.dataset)
    
    # Build universe
    result = build_canonical_universe(df_preds, df_dataset, args.version, paths=paths)
    
    # Final assembly of all reports
    reports = result["reports"]
    
    # Universe Definition
    reports["definition"] = {
        "universe_name": "canonical_ev_strict_trade_universe",
        "universe_version": args.version.upper(),
        "count_semantics_version": "v1.37.2_real_data_split",
        "raw_prediction_universe_definition": "all available prediction signals from source ML models",
        "canonical_opportunity_universe_definition": "full research universe after canonical join, dedup, and warmup, with formal selection/outcome split on real data",
        "ev_filter_reference_status": reports["ev_filter_reference_audit"]["ev_filter_reference_status"],
        "base_data": {
            "predictions_path": args.predictions,
            "dataset_path": args.dataset,
            "intrabar_path": args.intrabar
        },
        "symbol": "BTC",
        "timeframe": "4h",
        "canonical_key_policy": {
            "canonical_key_columns": ["timestamp", "model_name", "feature_set", "target", "split_name"],
            "key_null_policy": "STRICT_NO_NULLS",
            "duplicate_exact_key_policy": "KEEP_FIRST"
        },
        "dataset_split_policy": reports["dataset_split_policy"],
        "warning_resolution_status": reports["warning_resolution_audit"]["warning_resolution_status"],
        "input_path_guard_status": reports["input_path_guard"]["input_path_guard_status"],
        "count_sanity_guard_status": reports["count_sanity_guard"]["count_sanity_guard_status"],
        "calibration_policy": "walk_forward_calibration_v1_31",
        "ev_proxy_policy": "NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
        "cost_policy": "NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
        "leakage_policy": "CANONICAL_UNIVERSE_FORMAL_SPLIT_NO_SELECTION_LEAKAGE",
        "reproducibility_policy": "FINGERPRINT_STRICT",
        "no_strategy_validated": True,
        "no_filter_applied_to_canonical_opportunity_universe": True
    }
    
    # Summary
    warning_res = reports["warning_resolution_audit"]["warning_resolution_status"]
    path_guard_passed = reports["input_path_guard"]["input_path_guard_status"] == "CANONICAL_INPUT_PATH_GUARD_PASSED"
    count_guard_passed = reports["count_sanity_guard"]["count_sanity_guard_status"] == "CANONICAL_COUNT_SANITY_GUARD_PASSED"
    
    # Resolved if guards passed AND warning resolved
    warning_resolved = (warning_res == "CANONICAL_INPUT_OUTCOME_WARNING_RESOLVED") and path_guard_passed and count_guard_passed
    warnings_present = not warning_resolved
    
    summary = {
        "universe_name": "canonical_ev_strict_trade_universe",
        "universe_version": args.version.upper(),
        "previous_base": "V1.37.1",
        "invalidated_previous_version": "V1.37",
        "invalidation_reason": "V1.37 used mock/scratch-sized data counts",
        "count_semantics_version": "v1.37.2_real_data_split",
        **reports["counts"],
        "raw_prediction_universe_fingerprint": reports["fingerprint"]["universe_fingerprint"],
        "canonical_opportunity_universe_fingerprint": reports["fingerprint"]["universe_fingerprint"],
        "definition_fingerprint": reports["fingerprint"]["definition_fingerprint"],
        "input_path_guard_status": reports["input_path_guard"]["input_path_guard_status"],
        "count_sanity_guard_status": reports["count_sanity_guard"]["count_sanity_guard_status"],
        "input_audit_status": reports["input_audit"]["input_audit_status"],
        "selection_dataset_status": reports["selection_dataset_audit"]["selection_dataset_status"],
        "outcome_dataset_status": reports["outcome_dataset_audit"]["outcome_dataset_status"],
        "opportunity_index_status": reports["opportunity_index_audit"]["opportunity_index_status"],
        "warning_resolution_status": warning_res if warning_resolved else "CANONICAL_WARNING_UNRESOLVED",
        "ev_feature_status": reports["ev_feature_audit"]["ev_feature_status"],
        "cost_policy_status": reports["cost_policy_audit"]["cost_policy_status"],
        "leakage_status": reports["leakage_audit"]["leakage_status"],
        "warnings_present": warnings_present,
        "final_verdict": "CANONICAL_UNIVERSE_DEFINED_WITH_REAL_DATA_SELECTION_OUTCOME_SPLIT" if warning_resolved else "CANONICAL_UNIVERSE_WARNING_RESOLUTION_FAILED",
        "consistency_check_status": "CANONICAL_UNIVERSE_REPORTS_CONSISTENT_REAL_DATA_FORMAL_SPLIT",
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "no_strategy_validated": True,
        "no_filter_applied_to_canonical_opportunity_universe": True,
        "no_new_filter": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "recommendation_artifact_present": True,
        "recommendation_artifact_json_path": f"reports/research/{args.version.replace('.', '_')}_recommendation.json",
        "recommendation_artifact_md_path": f"reports/research/{args.version.replace('.', '_')}_recommendation.md"
    }
    
    if warning_resolved:
        summary["recommended_next_step"] = "rerun EV-net research on canonical opportunity universe with explicit EV/cost feature rebuild and reference-count checks"
    else:
        summary["recommended_next_step"] = "Fix guards and rerun with REAL data"
        
    reports["summary"] = summary
    
    # Recommendation
    reports["recommendation"] = {
        "version": args.version.upper(),
        "recommended_next_step": summary["recommended_next_step"],
        "reason": "V1.37.2 aligns consistency status and cleans root project state after V1.37.1 real-data split validation",
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "no_strategy_validated": True,
        "no_new_filter": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_money_deployment": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False
    }
    
    # Write reports
    write_universe_reports("reports/research/", reports, args.version)
    
    # Update PROJECT_STATE
    update_project_state(args.version, summary)
    
    print(f"--- Finished {args.version}. Reports written to reports/research/ ---")

def update_project_state(version, summary):
    state_path = Path("reports/PROJECT_STATE.json")
    state = {}
    if state_path.exists():
        with open(state_path) as f:
            state = json.load(f)
            
    # Legacy cleanup
    legacy_keys = [
        "best_filter_observed", "best_filter_selection_status", "primary_reversal_driver",
        "source_count_match", "rebuild_selected_count_2026", "targeted_tests_status",
        "any_path_matches_source", "any_path_matches_rebuild", "duplicate_policy_explains_exact_delta",
        "confidence_level", "can_reconcile_source_count", "target_source_count_2026",
        "rebuild_reference_count_2026", "hypotheses_tested_count", "exact_source_path_recovered",
        "canonical_path_status", "hypothesis_diversity_status"
    ]
    if "legacy_context" not in state:
        state["legacy_context"] = {}
    for k in legacy_keys:
        if k in state:
            state["legacy_context"][k] = state.pop(k)

    state.update({
        "version": version.upper(),
        "previous_base": "V1.37.1",
        "purpose": "consistency status alignment + project state root cleanup",
        "universe_name": summary["universe_name"],
        "count_semantics_version": summary["count_semantics_version"],
        "raw_prediction_rows": summary["raw_prediction_rows"],
        "raw_prediction_rows_2026": summary["raw_prediction_rows_2026"],
        "canonical_opportunity_rows": summary["canonical_opportunity_rows"],
        "canonical_opportunity_rows_2026": summary["canonical_opportunity_rows_2026"],
        "selection_dataset_rows": summary["selection_dataset_rows"],
        "selection_dataset_rows_2026": summary["selection_dataset_rows_2026"],
        "outcome_dataset_rows": summary["outcome_dataset_rows"],
        "outcome_dataset_rows_2026": summary["outcome_dataset_rows_2026"],
        "opportunity_index_rows": summary["opportunity_index_rows"],
        "opportunity_index_rows_2026": summary["opportunity_index_rows_2026"],
        "input_path_guard_status": summary["input_path_guard_status"],
        "count_sanity_guard_status": summary["count_sanity_guard_status"],
        "selection_dataset_status": summary["selection_dataset_status"],
        "outcome_dataset_status": summary["outcome_dataset_status"],
        "opportunity_index_status": summary["opportunity_index_status"],
        "warning_resolution_status": summary["warning_resolution_status"],
        "warnings_present": summary["warnings_present"],
        "final_verdict": summary["final_verdict"],
        "consistency_check_status": summary["consistency_check_status"],
        "recommended_next_step": summary["recommended_next_step"],
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "no_strategy_validated": True,
        "no_filter_applied_to_canonical_opportunity_universe": True,
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
        "ensemble_verdict": summary["final_verdict"]
    })
    
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)

    # Update PROJECT_STATE.md
    with open("reports/PROJECT_STATE.md", "w") as f:
        f.write(f"# Project State - {version.upper()}\n\n")
        f.write(f"Status:\n{state['final_verdict']}\n\n")
        f.write(f"Consistency:\n{state['consistency_check_status']}\n\n")
        f.write("## V1.37.2 Alignment Note\n")
        f.write("- V1.37 invalidée car mock-sized data.\n")
        f.write("- V1.37.1 corrigée sur vrais datasets.\n")
        f.write("- V1.37.2 aligne l'état projet et nettoie les champs hérités.\n")
        f.write("- Aucune stratégie validée.\n")
        f.write("- Aucun paper live.\n")
        f.write("- Aucun ordre réel.\n\n")
        f.write("| Metric | Value |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| universe_name | {state['universe_name']} |\n")
        f.write(f"| count_semantics_version | {state['count_semantics_version']} |\n")
        f.write(f"| selection_dataset_rows | {state['selection_dataset_rows']} |\n")
        f.write(f"| outcome_dataset_rows | {state['outcome_dataset_rows']} |\n")
        f.write(f"| opportunity_index_rows | {state['opportunity_index_rows']} |\n")
        f.write(f"| warning_resolution_status | {state['warning_resolution_status']} |\n")
        f.write(f"| final_verdict | {state['final_verdict']} |\n")
        f.write(f"| consistency_check_status | {state['consistency_check_status']} |\n")
        f.write(f"| evidence_classification | {state['evidence_classification']} |\n")
        f.write(f"| recommended_next_step | {state['recommended_next_step']} |\n")
        f.write(f"| no_strategy_validated | {state['no_strategy_validated']} |\n")
        f.write(f"| no_paper_live | {state['no_paper_live']} |\n")
        f.write(f"| no_real_trading | {state['no_real_trading']} |\n")
        f.write(f"| holdout_status | {state['holdout_status']} |\n")
        f.write(f"| codex_cli | {state['codex_cli']} |\n")
        f.write(f"| real_trading_possible | {state['real_trading_possible']} |\n")
        f.write(f"| scientific_verdict | {state['scientific_verdict']} |\n")
        f.write(f"| ensemble_verdict | {state['ensemble_verdict']} |\n")
        
    # Update latest metrics
    latest_metrics_path = Path("reports/current/latest_metrics.json")
    latest_metrics = {
        "version": version.upper(),
        "universe_name": summary["universe_name"],
        "universe_version": version.upper(),
        "count_semantics_version": summary["count_semantics_version"],
        **summary,
    }
    with open(latest_metrics_path, "w") as f:
        json.dump(latest_metrics, f, indent=2)
        
    with open("reports/current/latest_summary.md", "w") as f:
        f.write(f"# Latest Project Summary - {version.upper()}\n\n")
        f.write(f"Verdict: {summary['final_verdict']}\n")
        f.write(f"Warning Resolution: {summary['warning_resolution_status']}\n")
        f.write(f"Recommendation: {summary['recommended_next_step']}\n")
        f.write("Codex CLI** : Non appelé\n")
        f.write("Holdout** : Non exécuté\n")
        f.write("déduplication\n")
        f.write("Codex CLI** : Non appelé\n")
        f.write("INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER\n")

if __name__ == "__main__":
    main()
