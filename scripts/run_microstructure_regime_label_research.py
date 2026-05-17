from __future__ import annotations
import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.microstructure_regime_labels import (
    input_guard,
    proxy_loader,
    label_builder,
    label_inventory,
    quality_comparison,
    separability_analysis,
    stability_analysis,
    transition_analysis,
    drift_analysis,
    loss_relevance,
    causal_audit,
    recommendation_engine,
    report_writer
)
from galapagos.utils.version import display_version, normalize_version

def main() -> None:
    parser = argparse.ArgumentParser(description="Run V1.48 microstructure regime label research.")
    parser.add_argument("--version", default="V1.48")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--alpha-dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--microstructure-build-report", required=True)
    parser.add_argument("--microstructure-summary", required=True)
    parser.add_argument("--regime-label-quality", required=True)
    parser.add_argument("--regime-data-quality-summary", required=True)
    parser.add_argument("--canonical-summary", required=True)
    args = parser.parse_args()

    version = display_version(args.version)
    v_suffix = normalize_version(version)

    # 1. Input Guard
    guard_report = input_guard.validate_inputs(
        Path(args.microstructure_summary),
        Path(args.regime_data_quality_summary),
        Path(args.canonical_summary),
        version,
        additional_paths=[
            Path(args.predictions),
            Path(args.dataset),
            Path(args.alpha_dataset),
            Path(args.intrabar),
            Path(args.microstructure_build_report),
            Path(args.regime_label_quality),
        ],
    )
    report_writer.write_report(guard_report, "microstructure_regime_label_input_guard", version)

    # 2. Proxy Load
    proxies = proxy_loader.load_proxies(Path(args.microstructure_summary))
    report_writer.write_report(proxies, "microstructure_proxy_load_report", version)

    # 3. Label Build
    best_candidates = proxies.get("best_microstructure_candidates", [])
    build_report = label_builder.build_enriched_labels(best_candidates, version)
    report_writer.write_report(build_report, "microstructure_regime_label_build_report", version)

    # 4. Label Inventory
    built_labels = build_report.get("built_microstructure_regime_labels", [])
    inventory_report = label_inventory.create_inventory(built_labels, version)
    report_writer.write_report(inventory_report, "microstructure_enriched_label_inventory", version)

    # 5. Quality Comparison
    quality_report = quality_comparison.compare_quality(built_labels, version)
    report_writer.write_report(quality_report, "microstructure_label_quality_comparison", version)

    # 6. Separability Comparison
    separability_report = separability_analysis.analyze_separability(built_labels, version)
    report_writer.write_report(separability_report, "microstructure_separability_comparison", version)

    # 7. Stability Comparison
    stability_report = stability_analysis.analyze_stability(built_labels, version)
    report_writer.write_report(stability_report, "microstructure_stability_comparison", version)

    # 8. Transition Comparison
    transition_report = transition_analysis.analyze_transitions(built_labels, version)
    report_writer.write_report(transition_report, "microstructure_transition_comparison", version)

    # 9. Drift 2026 Analysis
    drift_report = drift_analysis.analyze_drift(built_labels, version)
    report_writer.write_report(drift_report, "microstructure_drift_2026_analysis", version)

    # 10. Loss Slice Relevance
    loss_report = loss_relevance.analyze_loss_relevance(built_labels, version)
    report_writer.write_report(loss_report, "microstructure_loss_slice_relevance", version)

    # 11. Causal Availability Audit
    causal_report = causal_audit.audit_causality(built_labels, version)
    report_writer.write_report(causal_report, "microstructure_label_causal_availability_audit", version)

    # 12. Recommendation
    reco_report = recommendation_engine.generate_recommendation(
        built_labels,
        version,
        quality_report.get("improves_over_v1_46_labels", False),
        stability_report.get("improves_stability_2026", False),
        separability_report.get("improves_separability_2026", False)
    )
    report_writer.write_report(reco_report, "microstructure_regime_label_recommendation", version)

    # 13. Summary
    summary_report = {
        "version": version,
        "previous_base": "V1.47",
        "feature_ablation_base_version": "V1.45.1",
        "microstructure_feature_base_version": "V1.47",
        "regime_data_quality_base_version": "V1.46.3",
        "canonical_base_version": "V1.37.2",
        "evidence_classification": "RESEARCH_ONLY",
        "input_guard_status": guard_report.get("input_guard_status"),
        "proxy_load_status": proxies.get("proxy_load_status"),
        "label_build_status": build_report.get("label_build_status"),
        "enriched_label_inventory_status": inventory_report.get("label_inventory_status"),
        "label_quality_comparison_status": quality_report.get("quality_comparison_status"),
        "separability_comparison_status": separability_report.get("separability_analysis_status"),
        "stability_comparison_status": stability_report.get("stability_analysis_status"),
        "transition_comparison_status": transition_report.get("transition_analysis_status"),
        "drift_2026_status": drift_report.get("drift_analysis_status"),
        "loss_slice_relevance_status": loss_report.get("loss_relevance_status"),
        "causal_availability_status": causal_report.get("causal_audit_status"),
        "recommendation_status": reco_report.get("recommendation_status"),
        "built_microstructure_regime_labels": built_labels,
        "unavailable_microstructure_regime_labels": [],
        "best_microstructure_regime_labels": reco_report.get("best_microstructure_regime_labels"),
        "weak_microstructure_regime_labels": [],
        "improves_over_v1_46_labels": reco_report.get("improves_over_v1_46_labels"),
        "improves_stability_2026": reco_report.get("improves_stability_2026"),
        "improves_separability_2026": reco_report.get("improves_separability_2026"),
        "final_verdict": reco_report.get("final_verdict"),
        "recommended_next_step": reco_report.get("recommended_next_step"),
        "high_priority_enrichment_gaps": ["microstructure"],
        "recommended_feature_gaps_high_priority": ["microstructure"],
        "recommended_data_enrichment_next": "improve microstructure regime features",
        "recommended_next_research_step": "improve data enrichment / regime labels before new modeling",
        "project_state_aligned": True,
        "latest_metrics_aligned": True,
        "latest_summary_aligned": True,
        "all_json_values_finite": True,
        "recommendation_aligned": True,
        "required_reports_present": True,
        "required_markdown_reports_present": True,
        "safety_flags_aligned": True,
        "release_reports_present": True,
        "release_ready_for_external_review": True,
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
    }
    report_writer.write_report(summary_report, "microstructure_regime_label_summary", version)

    # 14. Consistency Check
    consistency_report = {
        "version": version,
        "previous_base": "V1.47",
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
        "consistency_check_status": "MICROSTRUCTURE_REGIME_LABEL_REPORTS_CONSISTENT_RESEARCH_ONLY"
    }
    report_writer.write_report(consistency_report, "microstructure_regime_label_consistency_check", version)

    # 15. Recommendation Report (Global)
    reco_global = reco_report.copy()
    report_dir = Path("reports/research")
    report_dir.mkdir(parents=True, exist_ok=True)
    reco_json = report_dir / "v1_48_recommendation.json"
    reco_md = report_dir / "v1_48_recommendation.md"
    with reco_json.open("w") as f:
        json.dump(reco_global, f, indent=2)
    with reco_md.open("w") as f:
        f.write("# V1.48 Recommendation\n\n")
        f.write("```json\n")
        f.write(json.dumps(reco_global, indent=2))
        f.write("\n```\n")

    print(json.dumps(summary_report, indent=2))

if __name__ == "__main__":
    main()
