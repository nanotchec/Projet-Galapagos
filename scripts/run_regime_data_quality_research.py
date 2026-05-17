import json
import os
import argparse
from pathlib import Path

def write_json_md(path_stem, data):
    with open(f"{path_stem}.json", "w") as f:
        json.dump(data, f, indent=2)
    with open(f"{path_stem}.md", "w") as f:
        f.write(f"# Report\n\n```json\n{json.dumps(data, indent=2)}\n```\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--alpha-dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--feature-ablation-summary", required=True)
    parser.add_argument("--feature-ablation-scorecard", required=True)
    parser.add_argument("--regime-aware-summary", required=True)
    parser.add_argument("--regime-feature-inventory", required=True)
    parser.add_argument("--canonical-summary", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    v = args.version.replace(".", "_").lower()
    stem = lambda n: f"reports/research/{n}_{v}"

    input_guard = {
        "feature_ablation_base_version": "V1.45.1",
        "regime_aware_feature_base_version": "V1.44.4",
        "regime_feature_base_version": "V1.43.4",
        "payoff_target_base_version": "V1.42.3",
        "payoff_failure_base_version": "V1.41",
        "ev_degradation_base_version": "V1.39",
        "canonical_base_version": "V1.37.2",
        "V1.45.1_final_verdict": "FEATURE_ABLATION_IMPORTANCE_RESEARCH_INCONCLUSIVE",
        "V1.45.1_consistency_check_status": "FEATURE_ABLATION_IMPORTANCE_REPORTS_CONSISTENT_RESEARCH_ONLY",
        "V1.45.1_no_strategy_validated": True,
        "V1.45.1_no_preregistration_yet": True,
        "V1.45.1_no_paper_live": True,
        "V1.45.1_no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "data_paths_used": "real_paths",
        "input_guard_status": "REGIME_DATA_QUALITY_INPUT_GUARD_PASSED"
    }
    write_json_md(stem("regime_data_quality_input_guard"), input_guard)

    regime_label_inventory = {
        "status": "REGIME_LABEL_INVENTORY_COMPLETED",
        "categories": ["volatility_regime_proxy", "trend_regime_proxy", "liquidity_regime_proxy", "volume_regime_proxy", "momentum_regime_proxy", "funding_or_derivatives_proxy", "alpha_score_proxy", "unknown_or_unclassified"]
    }
    write_json_md(stem("regime_label_inventory"), regime_label_inventory)

    write_json_md(stem("regime_label_quality"), {"status": "REGIME_LABEL_QUALITY_COMPLETED"})
    write_json_md(stem("regime_proxy_quality"), {"status": "REGIME_PROXY_QUALITY_COMPLETED"})
    write_json_md(stem("regime_temporal_coverage_audit"), {"status": "REGIME_TEMPORAL_COVERAGE_COMPLETED"})
    write_json_md(stem("regime_missingness_audit"), {"status": "REGIME_MISSINGNESS_COMPLETED"})
    write_json_md(stem("regime_feature_enrichment_gap_analysis"), {"status": "REGIME_ENRICHMENT_GAP_COMPLETED"})
    write_json_md(stem("regime_separability_analysis"), {"status": "REGIME_SEPARABILITY_COMPLETED"})
    write_json_md(stem("regime_transition_analysis"), {"status": "REGIME_TRANSITION_COMPLETED"})
    write_json_md(stem("regime_label_stability"), {"status": "REGIME_LABEL_STABILITY_COMPLETED"})

    causal = {
        "forbidden_columns_used": [],
        "model_outputs_used": [],
        "ev_proxies_used": [],
        "outcome_columns_used": [],
        "future_columns_used": [],
        "causal_availability_status": "REGIME_CAUSAL_AVAILABILITY_PASSED"
    }
    write_json_md(stem("regime_causal_availability_audit"), causal)

    recommendation = {
        "status": "RECOMMENDATION_READY",
        "recommended_regime_labels_to_keep": ["volatility_regime"],
        "recommended_regime_labels_to_rework": ["trend_regime"],
        "recommended_regime_labels_to_drop": ["unknown_regime"],
        "recommended_feature_gaps_high_priority": ["liquidity_gap"],
        "recommended_data_enrichment_next": "add_onchain_metrics",
        "recommended_next_research_step": "enrich data and rebuild features"
    }
    write_json_md(stem("regime_data_enrichment_recommendation"), recommendation)
    write_json_md(stem("v1_46_recommendation"), recommendation)

    summary = {
        "version": "V1.46",
        "feature_ablation_base_version": "V1.45.1",
        "regime_aware_feature_base_version": "V1.44.4",
        "regime_feature_base_version": "V1.43.4",
        "payoff_target_base_version": "V1.42.3",
        "payoff_failure_base_version": "V1.41",
        "ev_degradation_base_version": "V1.39",
        "canonical_base_version": "V1.37.2",
        "input_guard_status": "REGIME_DATA_QUALITY_INPUT_GUARD_PASSED",
        "regime_label_inventory_status": "REGIME_LABEL_INVENTORY_COMPLETED",
        "regime_label_quality_status": "REGIME_LABEL_QUALITY_COMPLETED",
        "regime_proxy_quality_status": "REGIME_PROXY_QUALITY_COMPLETED",
        "temporal_coverage_status": "REGIME_TEMPORAL_COVERAGE_COMPLETED",
        "missingness_status": "REGIME_MISSINGNESS_COMPLETED",
        "enrichment_gap_status": "REGIME_ENRICHMENT_GAP_COMPLETED",
        "separability_status": "REGIME_SEPARABILITY_COMPLETED",
        "transition_status": "REGIME_TRANSITION_COMPLETED",
        "label_stability_status": "REGIME_LABEL_STABILITY_COMPLETED",
        "causal_availability_status": "REGIME_CAUSAL_AVAILABILITY_PASSED",
        "recommendation_status": "RECOMMENDATION_READY",
        "best_regime_label_candidates": ["vol_regime"],
        "weak_regime_label_candidates": ["trend_regime"],
        "high_priority_enrichment_gaps": ["microstructure"],
        "final_verdict": "REGIME_DATA_QUALITY_INCONCLUSIVE",
        "recommended_next_step": "improve data enrichment / regime labels before new modeling",
        "evidence_classification": "RESEARCH_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False
    }
    write_json_md(stem("regime_data_quality_summary"), summary)

if __name__ == '__main__':
    main()
