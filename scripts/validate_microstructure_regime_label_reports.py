from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_VERSION = "V1.48.1"
EXPECTED_PREVIOUS_BASE = "V1.48"
EXPECTED_CONSISTENCY_STATUS = "MICROSTRUCTURE_REGIME_LABEL_REPORTS_CONSISTENT_RESEARCH_ONLY"
EXPECTED_FINAL_VERDICT = "MICROSTRUCTURE_REGIME_LABELS_ACTIONABLE_BUT_UNVALIDATED"
EXPECTED_RECOMMENDED_NEXT_STEP = "rerun regime diagnostics with selected microstructure labels"
EXPECTED_FEATURE_BASE = "V1.47"
EXPECTED_DATA_QUALITY_BASE = "V1.46.3"
EXPECTED_CANONICAL_BASE = "V1.37.2"
EXPECTED_BEST_LABELS = ["amihud_illiquidity_regime", "realized_vol_proxy_regime"]
EXPECTED_WEAK_LABELS: list[str] = []
EXPECTED_REPO_FIELDS = {
    "high_priority_enrichment_gaps": ["microstructure"],
    "recommended_feature_gaps_high_priority": ["microstructure"],
    "recommended_data_enrichment_next": "improve microstructure regime features",
    "recommended_next_research_step": "improve data enrichment / regime labels before new modeling",
}
EXPECTED_REPORT_BASENAMES = [
    "microstructure_regime_label_input_guard_v1_48_1",
    "microstructure_proxy_load_report_v1_48_1",
    "microstructure_regime_label_build_report_v1_48_1",
    "microstructure_enriched_label_inventory_v1_48_1",
    "microstructure_label_quality_comparison_v1_48_1",
    "microstructure_separability_comparison_v1_48_1",
    "microstructure_stability_comparison_v1_48_1",
    "microstructure_transition_comparison_v1_48_1",
    "microstructure_drift_2026_analysis_v1_48_1",
    "microstructure_loss_slice_relevance_v1_48_1",
    "microstructure_label_causal_availability_audit_v1_48_1",
    "microstructure_regime_label_recommendation_v1_48_1",
    "microstructure_regime_label_summary_v1_48_1",
    "microstructure_regime_label_consistency_check_v1_48_1",
    "v1_48_1_recommendation",
]


def _load_json(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def _is_finite_json(value: object) -> bool:
    if isinstance(value, dict):
        return all(_is_finite_json(v) for v in value.values())
    if isinstance(value, list):
        return all(_is_finite_json(v) for v in value)
    if isinstance(value, float):
        return value == value and value not in (float("inf"), float("-inf"))
    return True


def _require(condition: bool, message: str, issues: list[str]) -> None:
    if not condition:
        issues.append(message)


def _check_alignment(summary: dict, project_state: dict, latest_metrics: dict, latest_summary: str, issues: list[str]) -> None:
    for key in [
        "version",
        "previous_base",
        "microstructure_feature_base_version",
        "regime_data_quality_base_version",
        "canonical_base_version",
        "final_verdict",
        "recommended_next_step",
        "evidence_classification",
        "consistency_check_status",
        "built_microstructure_regime_labels",
        "best_microstructure_regime_labels",
        "weak_microstructure_regime_labels",
        "improves_over_v1_46_labels",
        "improves_stability_2026",
        "improves_separability_2026",
        "project_state_aligned",
        "latest_metrics_aligned",
        "latest_summary_aligned",
        "all_json_values_finite",
        "required_reports_present",
        "required_markdown_reports_present",
        "safety_flags_aligned",
        "recommendation_aligned",
        "release_reports_present",
        "no_new_filter",
        "no_strategy_validated",
        "no_preregistration_yet",
        "no_paper_live",
        "no_real_trading",
        "holdout_executed",
        "codex_cli_called",
        "real_orders_possible",
    ]:
        _require(key in summary, f"summary missing {key}", issues)

    _require(summary.get("version") == EXPECTED_VERSION, "summary version mismatch", issues)
    _require(summary.get("previous_base") == EXPECTED_PREVIOUS_BASE, "summary previous_base mismatch", issues)
    _require(summary.get("microstructure_feature_base_version") == EXPECTED_FEATURE_BASE, "summary feature base mismatch", issues)
    _require(summary.get("regime_data_quality_base_version") == EXPECTED_DATA_QUALITY_BASE, "summary data quality base mismatch", issues)
    _require(summary.get("canonical_base_version") == EXPECTED_CANONICAL_BASE, "summary canonical base mismatch", issues)
    _require(summary.get("final_verdict") == EXPECTED_FINAL_VERDICT, "summary verdict mismatch", issues)
    _require(summary.get("recommended_next_step") == EXPECTED_RECOMMENDED_NEXT_STEP, "summary next step mismatch", issues)
    _require(summary.get("consistency_check_status") == EXPECTED_CONSISTENCY_STATUS, "summary consistency status mismatch", issues)
    _require(summary.get("best_microstructure_regime_labels") == EXPECTED_BEST_LABELS, "summary best labels mismatch", issues)
    _require(summary.get("weak_microstructure_regime_labels") == EXPECTED_WEAK_LABELS, "summary weak labels mismatch", issues)
    _require(summary.get("evidence_classification") in {"RESEARCH_ONLY", "DIAGNOSTIC_ONLY"}, "summary evidence classification invalid", issues)

    _require(summary.get("project_state_aligned") is True, "summary project_state_aligned not true", issues)
    _require(summary.get("latest_metrics_aligned") is True, "summary latest_metrics_aligned not true", issues)
    _require(summary.get("latest_summary_aligned") is True, "summary latest_summary_aligned not true", issues)
    _require(summary.get("all_json_values_finite") is True, "summary all_json_values_finite not true", issues)
    _require(summary.get("recommendation_aligned") is True, "summary recommendation_aligned not true", issues)
    _require(summary.get("required_reports_present") is True, "summary required_reports_present not true", issues)
    _require(summary.get("required_markdown_reports_present") is True, "summary required_markdown_reports_present not true", issues)
    _require(summary.get("safety_flags_aligned") is True, "summary safety_flags_aligned not true", issues)
    _require(summary.get("release_reports_present") is True, "summary release_reports_present not true", issues)
    _require(summary.get("no_new_filter") is True, "summary no_new_filter not true", issues)
    _require(summary.get("no_strategy_validated") is True, "summary no_strategy_validated not true", issues)
    _require(summary.get("no_preregistration_yet") is True, "summary no_preregistration_yet not true", issues)
    _require(summary.get("no_paper_live") is True, "summary no_paper_live not true", issues)
    _require(summary.get("no_real_trading") is True, "summary no_real_trading not true", issues)
    _require(summary.get("holdout_executed") is False, "summary holdout_executed not false", issues)
    _require(summary.get("codex_cli_called") is False, "summary codex_cli_called not false", issues)
    _require(summary.get("real_orders_possible") is False, "summary real_orders_possible not false", issues)

    _require(project_state.get("version") == EXPECTED_VERSION, "project state version mismatch", issues)
    _require(project_state.get("consistency_check_status") == EXPECTED_CONSISTENCY_STATUS, "project state consistency status missing or mismatch", issues)
    _require(project_state.get("no_strategy_validated") is True, "project state no_strategy_validated not true", issues)
    _require(project_state.get("no_preregistration_yet") is True, "project state no_preregistration_yet not true", issues)
    _require(project_state.get("no_paper_live") is True, "project state no_paper_live not true", issues)
    _require(project_state.get("no_real_trading") is True, "project state no_real_trading not true", issues)
    _require(project_state.get("holdout_executed") is False, "project state holdout_executed not false", issues)
    _require(project_state.get("codex_cli_called") is False, "project state codex_cli_called not false", issues)
    _require(project_state.get("real_orders_possible") is False, "project state real_orders_possible not false", issues)

    _require(latest_metrics.get("version") == EXPECTED_VERSION, "latest metrics version mismatch", issues)
    _require(latest_metrics.get("consistency_check_status") == EXPECTED_CONSISTENCY_STATUS, "latest metrics consistency status missing or mismatch", issues)

    _require("Version V1.48.1" in latest_summary, "latest summary text missing version", issues)
    _require("Previous base V1.48" in latest_summary, "latest summary text missing previous base", issues)
    _require("Verdict ACTIONABLE_BUT_UNVALIDATED" in latest_summary, "latest summary text missing verdict", issues)
    _require("Consistency Check PASSED" in latest_summary, "latest summary text missing consistency check", issues)
    _require("JSON finiteness PASSED" in latest_summary, "latest summary text missing JSON finiteness", issues)
    _require("No strategy validated" in latest_summary, "latest summary text missing no strategy validated", issues)
    _require("No preregistration" in latest_summary, "latest summary text missing no preregistration", issues)
    _require("No paper live" in latest_summary, "latest summary text missing no paper live", issues)
    _require("No real trading" in latest_summary, "latest summary text missing no real trading", issues)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate V1.48.1 microstructure regime label reports.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--allow-missing-release-reports", action="store_true")
    args = parser.parse_args()

    issues: list[str] = []
    _require(args.version.upper() == EXPECTED_VERSION, f"Unexpected version: {args.version}", issues)

    report_dir = Path("reports/research")
    for basename in EXPECTED_REPORT_BASENAMES:
        json_path = report_dir / f"{basename}.json"
        md_path = report_dir / f"{basename}.md"
        _require(json_path.exists(), f"Missing JSON report: {json_path}", issues)
        _require(md_path.exists(), f"Missing MD report: {md_path}", issues)

    summary = _load_json(report_dir / "microstructure_regime_label_summary_v1_48_1.json")
    consistency = _load_json(report_dir / "microstructure_regime_label_consistency_check_v1_48_1.json")
    recommendation = _load_json(report_dir / "v1_48_1_recommendation.json")
    project_state = _load_json(Path("reports/PROJECT_STATE.json"))
    latest_metrics = _load_json(Path("reports/current/latest_metrics.json"))
    latest_summary = Path("reports/current/latest_summary.md").read_text()

    _require(_is_finite_json(summary), "summary contains NaN/Infinity", issues)
    _require(_is_finite_json(consistency), "consistency contains NaN/Infinity", issues)
    _require(_is_finite_json(recommendation), "recommendation contains NaN/Infinity", issues)
    _require(_is_finite_json(project_state), "PROJECT_STATE contains NaN/Infinity", issues)
    _require(_is_finite_json(latest_metrics), "latest metrics contains NaN/Infinity", issues)

    verdict_str = str(summary.get("final_verdict")).upper()
    _require("UNVALIDATED" in verdict_str or "VALIDATED" not in verdict_str, "verdict contains VALIDATED", issues)
    for forbidden in ["preregistration", "paper live", "real trading"]:
        _require(forbidden not in str(summary.get("recommended_next_step")).lower(), f"recommended_next_step contains {forbidden}", issues)

    _require(consistency.get("version") == EXPECTED_VERSION, "consistency version mismatch", issues)
    _require(consistency.get("previous_base") == EXPECTED_PREVIOUS_BASE, "consistency previous_base mismatch", issues)
    _require(consistency.get("issues") == [], "consistency issues are not empty", issues)
    _require(consistency.get("consistency_check_status") == EXPECTED_CONSISTENCY_STATUS, "consistency status mismatch", issues)
    _require(consistency.get("project_state_aligned") is True, "consistency project_state_aligned not true", issues)
    _require(consistency.get("latest_metrics_aligned") is True, "consistency latest_metrics_aligned not true", issues)
    _require(consistency.get("latest_summary_aligned") is True, "consistency latest_summary_aligned not true", issues)
    _require(consistency.get("all_json_values_finite") is True, "consistency all_json_values_finite not true", issues)
    _require(consistency.get("required_reports_present") is True, "consistency required_reports_present not true", issues)
    _require(consistency.get("required_markdown_reports_present") is True, "consistency required_markdown_reports_present not true", issues)
    _require(consistency.get("safety_flags_aligned") is True, "consistency safety_flags_aligned not true", issues)
    _require(consistency.get("recommendation_aligned") is True, "consistency recommendation_aligned not true", issues)
    if not args.allow_missing_release_reports:
        _require(consistency.get("release_reports_present") is True, "consistency release_reports_present not true", issues)
    _require(consistency.get("status_field_policy") == "REMOVED", "consistency status_field_policy mismatch", issues)
    _require(consistency.get("status_field_present") is False, "consistency status_field_present not false", issues)

    _require(recommendation.get("version") == EXPECTED_VERSION, "recommendation version mismatch", issues)
    _require(recommendation.get("no_strategy_validated") is True, "recommendation safety flag mismatch", issues)
    _require(recommendation.get("no_preregistration_yet") is True, "recommendation safety flag mismatch", issues)
    _require(recommendation.get("no_paper_live") is True, "recommendation safety flag mismatch", issues)
    _require(recommendation.get("no_real_trading") is True, "recommendation safety flag mismatch", issues)
    _require(recommendation.get("holdout_executed") is False, "recommendation safety flag mismatch", issues)
    _require(recommendation.get("codex_cli_called") is False, "recommendation safety flag mismatch", issues)
    _require(recommendation.get("real_orders_possible") is False, "recommendation safety flag mismatch", issues)

    _check_alignment(summary, project_state, latest_metrics, latest_summary, issues)

    verdict = "VALIDATION PASSED" if not issues else "VALIDATION FAILED"
    print(verdict)
    if issues:
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

