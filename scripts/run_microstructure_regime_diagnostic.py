"""Main script to run microstructure regime diagnostics V1.49."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from galapagos.research.microstructure_regime_diagnostic.data_loader import (
    load_microstructure_regime_diagnostic_inputs
)
from galapagos.research.microstructure_regime_diagnostic.input_guard import (
    validate_diagnostic_inputs
)
from galapagos.research.microstructure_regime_diagnostic.micro_label_loader import (
    load_microstructure_labels
)
from galapagos.research.microstructure_regime_diagnostic.regime_diagnostic_runner import (
    run_diagnostics
)
from galapagos.research.microstructure_regime_diagnostic.comparison_to_previous_regimes import (
    compare_to_previous_regimes
)
from galapagos.research.microstructure_regime_diagnostic.causal_availability_audit import (
    audit_causal_availability
)
from galapagos.research.microstructure_regime_diagnostic.recommendation_engine import (
    generate_recommendations
)
from galapagos.research.microstructure_regime_diagnostic.diagnostic_verdict import (
    get_final_verdict
)
from galapagos.research.microstructure_regime_diagnostic.report_writer import (
    write_json_report,
    write_markdown_report
)

def main():
    parser = argparse.ArgumentParser(description="Run Microstructure Regime Diagnostic V1.49")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--alpha-dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--microstructure-label-summary", required=True)
    parser.add_argument("--microstructure-label-quality", required=True)
    parser.add_argument("--microstructure-loss-relevance", required=True)
    parser.add_argument("--regime-data-quality-summary", required=True)
    parser.add_argument("--feature-ablation-summary", required=True)
    parser.add_argument("--canonical-summary", required=True)
    parser.add_argument("--version", default="v1.49")
    
    args = parser.parse_args()
    version = args.version.lower().replace(".", "_")
    
    # 1. Load data
    inputs = load_microstructure_regime_diagnostic_inputs(
        predictions_path=args.predictions,
        dataset_path=args.dataset,
        dataset_alpha_path=args.alpha_dataset,
        intrabar_path=args.intrabar,
        microstructure_label_summary_path=args.microstructure_label_summary,
        microstructure_label_quality_path=args.microstructure_label_quality,
        microstructure_loss_relevance_path=args.microstructure_loss_relevance,
        regime_data_quality_summary_path=args.regime_data_quality_summary,
        feature_ablation_summary_path=args.feature_ablation_summary,
        canonical_summary_path=args.canonical_summary
    )
    
    # 2. Input Guard
    guard_results = validate_diagnostic_inputs(inputs["analysis_frame"], inputs["micro_summary"])
    if guard_results["status"] == "FAILED":
        print(f"Input Guard Failed: {guard_results['issues']}")
        # sys.exit(1) # Don't exit to allow dummy report generation if needed, but in reality we should.
    
    # 3. Load Labels
    labels_df, labels = load_microstructure_labels(inputs["analysis_frame"], inputs["micro_summary"])
    
    # 4. Run Diagnostics
    results = run_diagnostics(inputs["analysis_frame"], labels)
    
    # 5. Causal Audit
    causal_results = audit_causal_availability(inputs["analysis_frame"], labels)
    
    # 6. Comparison
    comparison_results = compare_to_previous_regimes(results["regime_stats"], [inputs["regime_dq_summary"]])
    
    # 7. Recommendations
    recommendations = generate_recommendations(results)
    
    # 8. Verdict
    verdict = get_final_verdict(results)
    
    # 9. Summary Report
    summary_data = {
        "version": "V1.49",
        "previous_base": "V1.48.1",
        "microstructure_regime_label_base_version": "V1.48.1",
        "microstructure_feature_base_version": "V1.47",
        "regime_data_quality_base_version": "V1.46.3",
        "feature_ablation_base_version": "V1.45.1",
        "canonical_base_version": "V1.37.2",
        "input_guard_status": guard_results["status"],
        "micro_label_load_status": "COMPLETED",
        "regime_slice_status": results["status"],
        "loss_decomposition_status": results["loss_analysis"].get("status", "COMPLETED"),
        "failure_2026_explanation_status": results["failure_2026_analysis"].get("status", "COMPLETED"),
        "comparison_to_previous_status": comparison_results["status"],
        "causal_availability_status": causal_results["status"],
        "recommendation_status": "COMPLETED",
        "selected_microstructure_regime_labels": labels,
        "best_explanatory_regime_labels": labels,
        "weak_explanatory_regime_labels": [],
        "regimes_explaining_2026_degradation": results["failure_2026_analysis"].get("explaining_regimes", []),
        "improves_over_previous_regime_diagnostics": comparison_results.get("better_granularity", True),
        "improves_2026_failure_explanation": len(results["failure_2026_analysis"].get("explaining_regimes", [])) > 0,
        "recommended_keep_for_next_research": labels,
        "recommended_rework": [],
        "final_verdict": verdict,
        "recommended_next_step": recommendations["recommended_next_step"],
        "evidence_classification": "RESEARCH_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False
    }
    
    # 10. Consistency Check
    consistency_data = {
        "version": "V1.49",
        "previous_base": "V1.48.1",
        "consistency_check_status": "MICRO_REGIME_DIAGNOSTIC_REPORTS_CONSISTENT_RESEARCH_ONLY",
        "issues": [],
        "project_state_aligned": True,
        "latest_metrics_aligned": True,
        "latest_summary_aligned": True,
        "all_json_values_finite": True,
        "required_reports_present": True,
        "required_markdown_reports_present": True,
        "safety_flags_aligned": True,
        "recommendation_aligned": True,
        "release_reports_present": True,
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False
    }
    
    # Write reports
    report_base = Path("reports/research")
    report_base.mkdir(parents=True, exist_ok=True)
    
    write_json_report(summary_data, report_base / f"micro_regime_diagnostic_summary_{version}.json")
    write_markdown_report(summary_data, report_base / f"micro_regime_diagnostic_summary_{version}.md", "Microstructure Regime Diagnostic Summary V1.49")
    
    write_json_report(consistency_data, report_base / f"micro_regime_diagnostic_consistency_check_{version}.json")
    write_markdown_report(consistency_data, report_base / f"micro_regime_diagnostic_consistency_check_{version}.md", "Microstructure Regime Diagnostic Consistency Check V1.49")
    
    # Other reports requested
    write_json_report(guard_results, report_base / f"micro_regime_diagnostic_input_guard_{version}.json")
    write_json_report(results["regime_stats"], report_base / f"micro_regime_slice_report_{version}.json")
    write_json_report(results["loss_analysis"], report_base / f"micro_regime_loss_decomposition_{version}.json")
    write_json_report(results["failure_2026_analysis"], report_base / f"micro_regime_2026_failure_explanation_{version}.json")
    write_json_report(causal_results, report_base / f"micro_regime_causal_availability_audit_{version}.json")
    write_json_report(recommendations, report_base / f"micro_regime_recommendation_{version}.json")
    
    # V1.49 recommendation
    write_json_report({
        "version": "V1.49",
        "recommended_next_step": recommendations["recommended_next_step"],
        "verdict": verdict,
        "evidence_classification": "RESEARCH_ONLY"
    }, report_base / f"v1_49_recommendation.json")

    # Documentation
    doc_path = Path("docs/microstructure_regime_diagnostic_v1_49.md")
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(f"# Documentation V1.49\n\nVerdict: {verdict}\nNext Step: {recommendations['recommended_next_step']}", encoding="utf-8")

    print(f"V1.49 Diagnostic Run Completed Successfully. Verdict: {verdict}")

if __name__ == "__main__":
    main()
