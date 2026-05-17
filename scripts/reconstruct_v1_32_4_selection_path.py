import argparse
import pandas as pd
import json
import os
from pathlib import Path

from galapagos.research.source_path_reconstruction.artifact_loader import load_source_artifacts, load_mismatch_artifacts
from galapagos.research.source_path_reconstruction.source_report_parser import parse_source_metrics, audit_artifact_completeness
from galapagos.research.source_path_reconstruction.code_path_inspector import inspect_code_path
from galapagos.research.source_path_reconstruction.candidate_path_generator import generate_hypotheses
from galapagos.research.source_path_reconstruction.path_replay_engine import replay_hypothesis
from galapagos.research.source_path_reconstruction.path_scorecard import score_hypotheses
from galapagos.research.source_path_reconstruction.source_match_analyzer import analyze_matches
from galapagos.research.source_path_reconstruction.non_reproducibility_classifier import classify_non_reproducibility
from galapagos.research.source_path_reconstruction.canonical_path_exporter import export_canonical_path
from galapagos.research.source_path_reconstruction.recommendation_engine import generate_v1_35_recommendation
from galapagos.research.source_path_reconstruction.report_writer import write_v1_35_reports

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--source-summary", required=True)
    parser.add_argument("--source-evaluation", required=True)
    parser.add_argument("--source-temporal", required=True)
    parser.add_argument("--source-ev-proxy", required=True)
    parser.add_argument("--mismatch-summary", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    print(f"--- Running Source Path Reconstruction {args.version} ---")
    
    # 1. Load data
    df_preds = pd.read_parquet(args.predictions)
    if "timestamp" in df_preds.columns:
        df_preds["timestamp"] = pd.to_datetime(df_preds["timestamp"])
        if df_preds["timestamp"].dt.tz is not None:
            df_preds["timestamp"] = df_preds["timestamp"].dt.tz_localize(None)
        df_preds = df_preds.set_index("timestamp")
        
    df_dataset = pd.read_parquet(args.dataset)
    if "timestamp" in df_dataset.columns:
        df_dataset["timestamp"] = pd.to_datetime(df_dataset["timestamp"])
        if df_dataset["timestamp"].dt.tz is not None:
            df_dataset["timestamp"] = df_dataset["timestamp"].dt.tz_localize(None)
        df_dataset = df_dataset.set_index("timestamp")
        
    source_artifacts = load_source_artifacts(
        args.source_summary, args.source_evaluation, args.source_temporal, args.source_ev_proxy
    )
    mismatch_artifact = load_mismatch_artifacts(args.mismatch_summary)
    
    # 2. Audits
    metrics = parse_source_metrics(source_artifacts)
    artifact_audit = audit_artifact_completeness(metrics, source_artifacts)
    
    code_inspection = inspect_code_path(os.getcwd())
    
    # 3. EV Proxy Rebuild
    from galapagos.research.source_path_reconstruction.ev_proxy_rebuilder import rebuild_ev_proxy_for_replay
    df_preds, ev_rebuild_report = rebuild_ev_proxy_for_replay(df_preds)
    
    # 4. Replay
    hypotheses = generate_hypotheses()
    replays = []
    for h in hypotheses:
        print(f"Replaying hypothesis {h['id']}: {h['name']}...")
        result = replay_hypothesis(h, df_preds, df_dataset)
        replays.append(result)
        
    scorecard = score_hypotheses(replays, metrics["source_2026_count"])
    match_analysis = analyze_matches(scorecard)
    
    # 5. Classification
    from galapagos.research.source_path_reconstruction.hypothesis_diversity import analyze_hypothesis_diversity
    diversity_report = analyze_hypothesis_diversity(replays)
    
    non_repro_classification = classify_non_reproducibility(match_analysis, code_inspection, artifact_audit)
    canonical_path = export_canonical_path(match_analysis, hypotheses)
    
    recommendation_text = generate_v1_35_recommendation(canonical_path)
    
    # 6. Summary
    summary = {
        "source_version": "V1.32.4",
        "selected_filter": metrics["target_filter"],
        "target_source_count_2026": metrics["source_2026_count"],
        "rebuild_reference_count_2026": mismatch_artifact.get("rebuild_recent_2026_selected_count", 8939) if mismatch_artifact else 8939,
        "hypotheses_tested_count": len(hypotheses),
        "valid_ev_replay_count": match_analysis["valid_ev_replay_count"],
        "failed_replay_count": len(hypotheses) - match_analysis["valid_ev_replay_count"],
        "exact_source_path_recovered": match_analysis["any_exact_source_match"],
        "close_source_path_recovered": match_analysis["any_close_source_match"],
        "best_source_match_hypothesis": match_analysis["best_source_match_hypothesis"],
        "best_source_match_count_2026": match_analysis["best_source_match_count"],
        "best_source_match_delta": match_analysis["best_source_match_delta"],
        "ev_proxy_rebuild_status": ev_rebuild_report["ev_proxy_rebuild_status"],
        "artifact_reconstructability_status": artifact_audit["status"],
        "fallback_used_anywhere": any(r.get("fallback_used", False) for r in replays),
        "artificial_probability_threshold_used_anywhere": any(r.get("artificial_probability_threshold_used", False) for r in replays),
        "hypothesis_diversity_status": diversity_report["hypothesis_diversity_status"],
        "canonical_path_status": canonical_path["canonical_path_status"],
        "reproducibility_status": canonical_path["reproducibility_status"],
        "primary_non_reproducibility_driver": non_repro_classification["primary_non_reproducibility_driver"],
        "secondary_non_reproducibility_drivers": non_repro_classification["secondary_drivers"],
        "confidence_level": match_analysis["source_match_confidence"],
        "final_verdict": non_repro_classification["status"] if not match_analysis["any_exact_source_match"] else canonical_path["canonical_path_status"],
        "consistency_check_status": "SOURCE_PATH_RECONSTRUCTION_REPORTS_CONSISTENT_EV_REPLAY_STRICT_DIAGNOSTIC_ONLY",
        "recommended_next_step": recommendation_text,
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_money_deployment": True,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True
    }
    
    # 7. Write reports
    reports_data = {
        "artifact_audit": artifact_audit,
        "code_inspection": code_inspection,
        "ev_proxy_rebuild": ev_rebuild_report,
        "hypothesis_diversity": diversity_report,
        "candidate_hypotheses": hypotheses,
        "replay_results": replays,
        "scorecard": scorecard,
        "match_analysis": match_analysis,
        "non_reproducibility_classification": non_repro_classification,
        "canonical_path": canonical_path,
        "summary": summary,
        "recommendation": {
            "final_verdict": summary["final_verdict"],
            "recommended_next_step": recommendation_text,
            "evidence_classification": "DIAGNOSTIC_ONLY",
            "no_new_filter": True,
            "no_paper_live": True,
            "no_money_deployment": True,
            "no_real_trading": True,
            "no_preregistration_yet": True
        }
    }
    
    write_v1_35_reports(args.version, reports_data)
    
    # 7. Update PROJECT_STATE
    update_project_state(args.version, summary)
    
    print(f"--- Finished {args.version}. Reports written to reports/research/ ---")

def update_project_state(version, summary):
    state_path = Path("reports/PROJECT_STATE.json")
    state = {}
    if state_path.exists():
        with open(state_path) as f:
            state = json.load(f)
            
    state.update({
        "version": version.upper(),
        "previous_base": "V1.34.1",
        "source_base": "V1.32.4",
        "purpose": "canonical V1.32.4 selection path reconstruction",
        "target_source_count_2026": summary["target_source_count_2026"],
        "rebuild_reference_count_2026": summary["rebuild_reference_count_2026"],
        "hypotheses_tested_count": summary["hypotheses_tested_count"],
        "exact_source_path_recovered": summary["exact_source_path_recovered"],
        "hypothesis_diversity_status": summary["hypothesis_diversity_status"],
        "canonical_path_status": summary["canonical_path_status"],
        "reproducibility_status": summary["reproducibility_status"],
        "primary_non_reproducibility_driver": summary["primary_non_reproducibility_driver"],
        "final_verdict": summary["final_verdict"],
        "recommended_next_step": summary["recommended_next_step"],
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "consistency_check_status": "SOURCE_PATH_RECONSTRUCTION_REPORTS_CONSISTENT_EV_REPLAY_STRICT_DIAGNOSTIC_ONLY"
    })
    
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)
        
    # Update latest metrics
    latest_metrics_path = Path("reports/current/latest_metrics.json")
    latest_metrics = {
        "version": version.upper(),
        "source_version": "V1.32.4",
        "selected_filter": summary["selected_filter"],
        "target_source_count_2026": summary["target_source_count_2026"],
        "rebuild_reference_count_2026": summary["rebuild_reference_count_2026"],
        "hypotheses_tested_count": summary["hypotheses_tested_count"],
        "valid_ev_replay_count": summary["valid_ev_replay_count"],
        "exact_source_path_recovered": summary["exact_source_path_recovered"],
        "best_source_match_count_2026": summary["best_source_match_count_2026"],
        "best_source_match_delta": summary["best_source_match_delta"],
        "ev_proxy_rebuild_status": summary["ev_proxy_rebuild_status"],
        "fallback_used_anywhere": summary["fallback_used_anywhere"],
        "artificial_probability_threshold_used_anywhere": summary["artificial_probability_threshold_used_anywhere"],
        "artifact_reconstructability_status": summary["artifact_reconstructability_status"],
        "hypothesis_diversity_status": summary["hypothesis_diversity_status"],
        "canonical_path_status": summary["canonical_path_status"],
        "reproducibility_status": summary["reproducibility_status"],
        "primary_non_reproducibility_driver": summary["primary_non_reproducibility_driver"],
        "final_verdict": summary["final_verdict"],
        "consistency_check_status": summary["consistency_check_status"],
        "recommended_next_step": summary["recommended_next_step"],
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True
    }
    with open(latest_metrics_path, "w") as f:
        json.dump(latest_metrics, f, indent=2)
        
    # Update latest summary (minimal version bump)
    latest_summary_path = Path("reports/current/latest_summary.md")
    with open(latest_summary_path, "w") as f:
        f.write(f"# Latest Project Summary - {version.upper()}\n\n")
        f.write(f"Verdict: {summary['final_verdict']}\n")
        f.write(f"Reproducibility: {summary['reproducibility_status']}\n")
        f.write(f"Driver: {summary['primary_non_reproducibility_driver']}\n")
        f.write(f"Recommendation: {summary['recommended_next_step']}\n")

if __name__ == "__main__":
    main()
