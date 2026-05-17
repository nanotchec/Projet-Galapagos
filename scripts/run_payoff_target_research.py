"""Main execution script for Galapagos V1.42 Payoff Target Research."""
from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import bootstrap_src_path
bootstrap_src_path()

from galapagos.research.payoff_target_research.data_loader import load_research_inputs
from galapagos.research.payoff_target_research.input_guard import validate_research_inputs
from galapagos.research.payoff_target_research.horizon_builder import build_horizon_candidates
from galapagos.research.payoff_target_research.target_definitions import define_exploratory_targets
from galapagos.research.payoff_target_research.target_noise_analysis import analyze_target_noise
from galapagos.research.payoff_target_research.downside_label_analysis import analyze_downside_labels
from galapagos.research.payoff_target_research.horizon_walk_forward_eval import run_horizon_walk_forward_eval
from galapagos.research.payoff_target_research.target_baseline_comparison import compare_targets_to_baselines
from galapagos.research.payoff_target_research.temporal_robustness import analyze_temporal_robustness
from galapagos.research.payoff_target_research.regime_breakdown import analyze_regime_breakdown
from galapagos.research.payoff_target_research.overfit_guard import check_overfit_risk
from galapagos.research.payoff_target_research.diagnostic_verdict import formulate_verdict
from galapagos.research.payoff_target_research.report_writer import write_json_report, write_md_report

def main():
    parser = argparse.ArgumentParser(description="Run V1.42 Payoff Target Research")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--failure-summary", required=True)
    parser.add_argument("--payoff-summary", required=True)
    parser.add_argument("--diagnostic-summary", required=True)
    parser.add_argument("--version", default="v1.42")
    args = parser.parse_args()

    # 1. Load inputs
    inputs = load_research_inputs(
        predictions_path=args.predictions,
        dataset_path=args.dataset,
        intrabar_path=args.intrabar,
        failure_summary_path=args.failure_summary,
        payoff_summary_path=args.payoff_summary,
        diagnostic_summary_path=args.diagnostic_summary,
    )

    # 2. Input Guard
    guard_results = validate_research_inputs(inputs)
    write_json_report(guard_results, f"reports/research/payoff_target_input_guard_{args.version}.json")
    write_md_report(f"Payoff Target Input Guard {args.version}", guard_results, f"reports/research/payoff_target_input_guard_{args.version}.md")

    if guard_results["status"] == "PAYOFF_TARGET_INPUT_GUARD_FAILED":
        print("Input guard failed. See reports for details.")
        return

    # 2.1 Count Semantics
    from galapagos.research.payoff_target_research.count_semantics import clarify_count_semantics
    count_results = clarify_count_semantics(inputs["predictions"], inputs["dataset"])
    write_json_report(count_results, f"reports/research/payoff_target_count_semantics_{args.version}.json")
    write_md_report(f"Payoff Target Count Semantics {args.version}", count_results, f"reports/research/payoff_target_count_semantics_{args.version}.md")

    # 3. Horizon Candidates
    horizon_results = build_horizon_candidates(inputs["analysis_frame"])
    write_json_report(horizon_results, f"reports/research/payoff_target_horizon_candidates_{args.version}.json")
    write_md_report(f"Payoff Target Horizon Candidates {args.version}", horizon_results, f"reports/research/payoff_target_horizon_candidates_{args.version}.md")

    # 4. Target Definitions
    labeled_frame, target_results = define_exploratory_targets(inputs["analysis_frame"], horizon="forward_return_12bar")
    write_json_report(target_results, f"reports/research/payoff_target_definitions_{args.version}.json")
    write_md_report(f"Payoff Target Definitions {args.version}", target_results, f"reports/research/payoff_target_definitions_{args.version}.md")

    # 5. Noise Analysis
    noise_results = analyze_target_noise(labeled_frame, target_results)
    write_json_report(noise_results, f"reports/research/payoff_target_noise_analysis_{args.version}.json")
    write_md_report(f"Payoff Target Noise Analysis {args.version}", noise_results, f"reports/research/payoff_target_noise_analysis_{args.version}.md")

    # 6. Downside Label Analysis
    downside_results = analyze_downside_labels(labeled_frame, target_results)
    write_json_report(downside_results, f"reports/research/payoff_downside_label_analysis_{args.version}.json")
    write_md_report(f"Payoff Downside Label Analysis {args.version}", downside_results, f"reports/research/payoff_downside_label_analysis_{args.version}.md")

    # 7. Walk-Forward Eval
    wf_results = run_horizon_walk_forward_eval(labeled_frame, target_results)
    write_json_report(wf_results, f"reports/research/payoff_target_horizon_walk_forward_eval_{args.version}.json")
    write_md_report(f"Payoff Target Horizon Walk-Forward Eval {args.version}", wf_results, f"reports/research/payoff_target_horizon_walk_forward_eval_{args.version}.md")

    # 8. Baseline Comparison
    baseline_results = compare_targets_to_baselines(wf_results, inputs["payoff_summary"])
    write_json_report(baseline_results, f"reports/research/payoff_target_baseline_comparison_{args.version}.json")
    write_md_report(f"Payoff Target Baseline Comparison {args.version}", baseline_results, f"reports/research/payoff_target_baseline_comparison_{args.version}.md")

    # 9. Temporal / Regime Robustness
    temporal_results = analyze_temporal_robustness(labeled_frame, target_results)
    write_json_report(temporal_results, f"reports/research/payoff_target_temporal_robustness_{args.version}.json")
    write_md_report(f"Payoff Target Temporal Robustness {args.version}", temporal_results, f"reports/research/payoff_target_temporal_robustness_{args.version}.md")

    regime_results = analyze_regime_breakdown(labeled_frame, target_results)
    write_json_report(regime_results, f"reports/research/payoff_target_regime_breakdown_{args.version}.json")
    write_md_report(f"Payoff Target Regime Breakdown {args.version}", regime_results, f"reports/research/payoff_target_regime_breakdown_{args.version}.md")

    # 10. Overfit Guard
    overfit_results = check_overfit_risk(len(horizon_results["candidates"]), len(target_results["targets"]))
    write_json_report(overfit_results, f"reports/research/payoff_target_overfit_guard_{args.version}.json")
    write_md_report(f"Payoff Target Overfit Guard {args.version}", overfit_results, f"reports/research/payoff_target_overfit_guard_{args.version}.md")

    # 10.1 JSON Finiteness Audit
    from galapagos.research.payoff_target_research.json_finiteness_audit import audit_json_finiteness
    finiteness_results = audit_json_finiteness("reports/research", pattern=f"*{args.version}.json")
    write_json_report(finiteness_results, f"reports/research/payoff_target_json_finiteness_audit_{args.version}.json")
    write_md_report(f"Payoff Target JSON Finiteness Audit {args.version}", finiteness_results, f"reports/research/payoff_target_json_finiteness_audit_{args.version}.md")

    # 11. Verdict
    combined_results = {
        "baseline_comparison": baseline_results,
        "target_noise": noise_results,
    }
    verdict_results = formulate_verdict(combined_results)
    
    # 12. Summary
    summary = {
        "version": args.version.upper(),
        "failure_diagnostic_base": guard_results["failure_diagnostic_base"],
        "payoff_objective_base_version": guard_results["payoff_objective_base_version"],
        "diagnostic_base": guard_results["diagnostic_base"],
        "canonical_base_version": guard_results["canonical_base_version"],
        "input_guard_status": guard_results["status"],
        "count_semantics_status": count_results["status"],
        "horizon_candidate_status": horizon_results["status"],
        "target_definition_status": target_results["status"],
        "target_noise_status": noise_results["status"],
        "downside_label_status": downside_results["status"],
        "horizon_walk_forward_status": wf_results["status"],
        "baseline_comparison_status": baseline_results["status"],
        "temporal_robustness_status": temporal_results["status"],
        "regime_breakdown_status": regime_results["status"],
        "overfit_guard_status": overfit_results["status"],
        "json_finiteness_status": finiteness_results["status"],
        "best_target_observed": baseline_results["best_target_observed"],
        "best_horizon_observed": target_results["horizon_used"],
        "best_target_2026_metric": baseline_results["best_target_2026_metric"],
        "best_target_downside_metric": baseline_results["best_target_downside_metric"],
        "beats_v1_40_1_target": baseline_results["beats_v1_40_1_target"],
        "beats_probability_baseline": baseline_results["beats_probability_baseline"],
        "beats_ev_proxy_baseline": baseline_results["beats_ev_proxy_baseline"],
        "beats_random_baseline": baseline_results["beats_random_baseline"],
        "recent_window_status": temporal_results["recent_window_status"],
        "final_verdict": verdict_results["final_verdict"],
        "recommended_next_step": verdict_results["recommended_next_step"],
        "evidence_classification": "EXPLORATORY_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False
    }
    write_json_report(summary, f"reports/research/payoff_target_research_summary_{args.version}.json")
    write_md_report(f"Payoff Target Research Summary {args.version}", summary, f"reports/research/payoff_target_research_summary_{args.version}.md")
    
    # Recommandation
    rec = {
        "recommended_next_step": verdict_results["recommended_next_step"],
        "evidence_classification": "EXPLORATORY_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False
    }
    write_json_report(rec, f"reports/research/{args.version}_recommendation.json")
    write_md_report(f"{args.version.upper()} Recommendation", rec, f"reports/research/{args.version}_recommendation.md")

    print(f"{args.version.upper()} research complete. Final verdict: {verdict_results['final_verdict']}")

if __name__ == "__main__":
    main()
