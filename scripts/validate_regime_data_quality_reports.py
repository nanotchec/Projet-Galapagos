import json
import argparse
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.utils.version import display_version, normalize_version

def write_json_md(path_stem, data):
    with open(f"{path_stem}.json", "w") as f:
        json.dump(data, f, indent=2)
    with open(f"{path_stem}.md", "w") as f:
        f.write(f"# Report\n\n```json\n{json.dumps(data, indent=2)}\n```\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    version = display_version(args.version)
    v = normalize_version(args.version)

    consistency_file = f"reports/research/regime_data_quality_consistency_check_{v}.json"
    if not Path(consistency_file).exists():
        print(f"Missing consistency check: {consistency_file}")
        exit(1)
        
    with open(consistency_file) as f:
        consistency = json.load(f)

    # Required fields in consistency check
    required_fields = [
        "version", "previous_base", "consistency_check_status", "issues",
        "project_state_aligned", "latest_metrics_aligned", "latest_summary_aligned",
        "all_json_values_finite", "required_reports_present",
        "required_markdown_reports_present", "safety_flags_aligned",
        "recommendation_aligned", "release_reports_present",
        "status_field_policy", "status_field_present",
        "no_new_filter", "no_strategy_validated", "no_preregistration_yet",
        "no_paper_live", "no_real_trading", "holdout_executed", "codex_cli_called"
    ]
    for field in required_fields:
        assert field in consistency, f"Missing field: {field}"

    assert consistency["version"] == version
    assert consistency["previous_base"] == "V1.46.2"
    assert consistency["consistency_check_status"] == "REGIME_DATA_QUALITY_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY"
    assert consistency["issues"] == []
    assert consistency["project_state_aligned"] is True
    assert consistency["latest_metrics_aligned"] is True
    assert consistency["latest_summary_aligned"] is True
    assert consistency["all_json_values_finite"] is True
    assert consistency["required_reports_present"] is True
    assert consistency["required_markdown_reports_present"] is True
    assert consistency["safety_flags_aligned"] is True
    assert consistency["recommendation_aligned"] is True
    assert consistency["release_reports_present"] is True
    assert consistency["status_field_policy"] == "REMOVED"
    assert consistency["status_field_present"] is False
    assert consistency["no_new_filter"] is True
    assert consistency["no_strategy_validated"] is True
    assert consistency["no_preregistration_yet"] is True
    assert consistency["no_paper_live"] is True
    assert consistency["no_real_trading"] is True
    assert consistency["holdout_executed"] is False
    assert consistency["codex_cli_called"] is False

    # V1.46.3 specific recommendation alignment
    if v == "v1_46_3":
        recommendation_file = f"reports/research/regime_data_quality_recommendation_{v}.json"
        with open(recommendation_file) as f:
            rec = json.load(f)
        assert rec["high_priority_enrichment_gaps"] == ["microstructure"]
        assert rec["recommended_feature_gaps_high_priority"] == ["microstructure"]
        assert rec["recommended_data_enrichment_next"] == "improve microstructure regime features"
        assert rec["recommended_next_research_step"] == "improve data enrichment / regime labels before new modeling"
        assert rec["recommended_next_step"] == "improve data enrichment / regime labels before new modeling"

    # Cross-check with PROJECT_STATE.json
    with open("reports/PROJECT_STATE.json") as f:
        project_state = json.load(f)
    assert project_state["version"] == version
    assert project_state["previous_base"] == "V1.46.2"
    assert project_state["status_field_policy"] == "REMOVED"
    assert project_state["status_field_present"] is False
    assert project_state["high_priority_enrichment_gaps"] == ["microstructure"]
    assert project_state["recommended_feature_gaps_high_priority"] == ["microstructure"]
    assert project_state["recommended_data_enrichment_next"] == "improve microstructure regime features"
    assert project_state["recommended_next_research_step"] == "improve data enrichment / regime labels before new modeling"

    # Cross-check with latest_metrics.json
    with open("reports/current/latest_metrics.json") as f:
        latest_metrics = json.load(f)
    assert latest_metrics["version"] == version
    assert latest_metrics["previous_base"] == "V1.46.2"
    assert latest_metrics["high_priority_enrichment_gaps"] == ["microstructure"]
    assert latest_metrics["recommended_feature_gaps_high_priority"] == ["microstructure"]
    assert latest_metrics["recommended_data_enrichment_next"] == "improve microstructure regime features"
    assert latest_metrics["recommended_next_research_step"] == "improve data enrichment / regime labels before new modeling"

    summary_file = f"reports/research/regime_data_quality_summary_{v}.json"
    with open(summary_file) as f:
        summary = json.load(f)

    causal_file = f"reports/research/regime_causal_availability_audit_{v}.json"
    if not Path(causal_file).exists():
        # Fallback to base version if not yet created for v1.46.2
        # But for v1.46.2 we should probably have it
        pass

    assert summary["version"] == version
    assert summary["previous_base"] == "V1.46.2"
    assert "NaN" not in json.dumps(summary)
    assert "VALIDATED" not in summary["final_verdict"]
    assert "preregistration" not in summary["recommended_next_step"].lower()
    assert "paper live" not in summary["recommended_next_step"].lower()
    assert "real trading" not in summary["recommended_next_step"].lower()
    assert summary["high_priority_enrichment_gaps"] == ["microstructure"]
    assert summary["recommended_feature_gaps_high_priority"] == ["microstructure"]
    assert summary["recommended_data_enrichment_next"] == "improve microstructure regime features"
    assert summary["recommended_next_research_step"] == "improve data enrichment / regime labels before new modeling"
    assert summary["no_strategy_validated"] is True
    assert summary["no_preregistration_yet"] is True
    assert summary["no_paper_live"] is True
    assert summary["no_real_trading"] is True
    assert summary["holdout_executed"] is False
    assert summary["codex_cli_called"] is False

    if version == "V1.46.3":
        expected_recommendation = {
            "high_priority_enrichment_gaps": ["microstructure"],
            "recommended_feature_gaps_high_priority": ["microstructure"],
            "recommended_data_enrichment_next": "improve microstructure regime features",
            "recommended_next_research_step": "improve data enrichment / regime labels before new modeling",
            "recommended_next_step": "improve data enrichment / regime labels before new modeling",
        }
        consistency_recommendation = consistency.get("canonical_recommendation")
        assert consistency_recommendation == expected_recommendation, consistency_recommendation
        assert summary["recommended_next_step"] == expected_recommendation["recommended_next_step"]

    print(f"Validation PASSED for version {version}")

if __name__ == '__main__':
    main()
