from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED_VERSION = "V1.47"
EXPECTED_PREVIOUS_BASE = "V1.46.3"
EXPECTED_CONSISTENCY_STATUS = "MICROSTRUCTURE_REGIME_FEATURE_REPORTS_CONSISTENT_RESEARCH_ONLY"
EXPECTED_FINAL_VERDICT = "MICROSTRUCTURE_REGIME_FEATURES_ACTIONABLE_BUT_UNVALIDATED"
EXPECTED_RECOMMENDED_NEXT_STEP = "improve data enrichment / regime labels before new modeling"
EXPECTED_RECOMMENDED_DATA_ENRICHMENT = "improve microstructure regime features"
EXPECTED_RECOMMENDED_FEATURE_GAPS = ["microstructure"]
EXPECTED_REPORT_BASENAMES = [
    "microstructure_input_guard_v1_47",
    "microstructure_feature_inventory_v1_47",
    "microstructure_feature_build_report_v1_47",
    "microstructure_causal_availability_audit_v1_47",
    "microstructure_coverage_audit_v1_47",
    "microstructure_missingness_audit_v1_47",
    "microstructure_stability_analysis_v1_47",
    "microstructure_regime_relevance_analysis_v1_47",
    "microstructure_feature_quality_scorecard_v1_47",
    "microstructure_enrichment_recommendation_v1_47",
    "microstructure_regime_feature_summary_v1_47",
    "microstructure_regime_feature_consistency_check_v1_47",
    "v1_47_recommendation",
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate V1.47 microstructure regime feature reports.")
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--allow-missing-release-reports",
        action="store_true",
        help="Allow running before release/audit/smoke reports are materialized.",
    )
    args = parser.parse_args()

    issues: list[str] = []
    if args.version.upper() != EXPECTED_VERSION:
        issues.append(f"Unexpected version: {args.version}")

    report_dir = Path("reports/research")
    state_path = Path("reports/PROJECT_STATE.json")
    latest_metrics_path = Path("reports/current/latest_metrics.json")
    latest_summary_path = Path("reports/current/latest_summary.md")
    release_report_path = Path("reports/release_zip_v1_47.json")
    audit_report_path = Path("reports/zip_audit_v1_47.json")
    smoke_report_path = Path("reports/zip_smoke_test_v1_47.json")

    for basename in EXPECTED_REPORT_BASENAMES:
        json_path = report_dir / f"{basename}.json"
        md_path = report_dir / f"{basename}.md"
        _require(json_path.exists(), f"Missing JSON report: {json_path}", issues)
        _require(md_path.exists(), f"Missing MD report: {md_path}", issues)

    _require(state_path.exists(), "Missing PROJECT_STATE.json", issues)
    _require(latest_metrics_path.exists(), "Missing latest_metrics.json", issues)
    _require(latest_summary_path.exists(), "Missing latest_summary.md", issues)
    if not args.allow_missing_release_reports:
        _require(release_report_path.exists(), "Missing release report", issues)
        _require(audit_report_path.exists(), "Missing audit report", issues)
        _require(smoke_report_path.exists(), "Missing smoke report", issues)

    summary = _load_json(report_dir / "microstructure_regime_feature_summary_v1_47.json")
    consistency = _load_json(report_dir / "microstructure_regime_feature_consistency_check_v1_47.json")
    recommendation = _load_json(report_dir / "v1_47_recommendation.json")
    state = _load_json(state_path)
    latest_metrics = _load_json(latest_metrics_path)
    release_report = _load_json(release_report_path) if release_report_path.exists() else {}
    audit_report = _load_json(audit_report_path) if audit_report_path.exists() else {}
    smoke_report = _load_json(smoke_report_path) if smoke_report_path.exists() else {}

    for name, payload in [
        ("summary", summary),
        ("consistency", consistency),
        ("recommendation", recommendation),
        ("state", state),
        ("latest_metrics", latest_metrics),
        ("release_report", release_report),
        ("audit_report", audit_report),
        ("smoke_report", smoke_report),
    ]:
        _require(_is_finite_json(payload), f"{name} contains NaN/Infinity", issues)

    _require(summary.get("version") == EXPECTED_VERSION, "summary version mismatch", issues)
    _require(summary.get("previous_base") == EXPECTED_PREVIOUS_BASE, "summary previous_base mismatch", issues)
    _require(summary.get("final_verdict") == EXPECTED_FINAL_VERDICT, "summary verdict mismatch", issues)
    _require(summary.get("recommended_next_step") == EXPECTED_RECOMMENDED_NEXT_STEP, "summary next step mismatch", issues)
    _require(summary.get("recommended_data_enrichment_next") == EXPECTED_RECOMMENDED_DATA_ENRICHMENT, "summary enrichment mismatch", issues)
    _require(summary.get("recommended_feature_gaps_high_priority") == EXPECTED_RECOMMENDED_FEATURE_GAPS, "summary feature gaps mismatch", issues)

    _require(consistency.get("version") == EXPECTED_VERSION, "consistency version mismatch", issues)
    _require(consistency.get("previous_base") == EXPECTED_PREVIOUS_BASE, "consistency previous_base mismatch", issues)
    _require(consistency.get("issues") == [], "consistency issues must be empty", issues)
    _require(consistency.get("consistency_check_status") == EXPECTED_CONSISTENCY_STATUS, "consistency status mismatch", issues)
    _require(consistency.get("project_state_aligned") is True, "project_state_aligned must be true", issues)
    _require(consistency.get("latest_metrics_aligned") is True, "latest_metrics_aligned must be true", issues)
    _require(consistency.get("latest_summary_aligned") is True, "latest_summary_aligned must be true", issues)
    _require(consistency.get("all_json_values_finite") is True, "all_json_values_finite must be true", issues)
    _require(consistency.get("required_reports_present") is True, "required_reports_present must be true", issues)
    _require(consistency.get("required_markdown_reports_present") is True, "required_markdown_reports_present must be true", issues)
    _require(consistency.get("safety_flags_aligned") is True, "safety_flags_aligned must be true", issues)
    _require(consistency.get("recommendation_aligned") is True, "recommendation_aligned must be true", issues)
    _require(consistency.get("release_reports_present") is True, "release_reports_present must be true", issues)
    _require(consistency.get("status_field_policy") == "REMOVED", "status_field_policy must be REMOVED", issues)
    _require(consistency.get("status_field_present") is False, "status_field_present must be false", issues)
    _require(consistency.get("canonical_recommendation", {}).get("high_priority_enrichment_gaps") == EXPECTED_RECOMMENDED_FEATURE_GAPS, "canonical high_priority_enrichment_gaps mismatch", issues)
    _require(consistency.get("canonical_recommendation", {}).get("recommended_feature_gaps_high_priority") == EXPECTED_RECOMMENDED_FEATURE_GAPS, "canonical recommended_feature_gaps_high_priority mismatch", issues)
    _require(consistency.get("canonical_recommendation", {}).get("recommended_data_enrichment_next") == EXPECTED_RECOMMENDED_DATA_ENRICHMENT, "canonical recommended_data_enrichment_next mismatch", issues)
    _require(consistency.get("canonical_recommendation", {}).get("recommended_next_research_step") == EXPECTED_RECOMMENDED_NEXT_STEP, "canonical recommended_next_research_step mismatch", issues)
    _require(consistency.get("canonical_recommendation", {}).get("recommended_next_step") == EXPECTED_RECOMMENDED_NEXT_STEP, "canonical recommended_next_step mismatch", issues)

    _require(recommendation.get("version") == EXPECTED_VERSION, "recommendation version mismatch", issues)
    _require(recommendation.get("recommended_next_step") == EXPECTED_RECOMMENDED_NEXT_STEP, "recommendation next step mismatch", issues)
    _require(recommendation.get("recommended_data_enrichment_next") == EXPECTED_RECOMMENDED_DATA_ENRICHMENT, "recommendation enrichment mismatch", issues)
    _require(recommendation.get("recommended_feature_gaps_high_priority") == EXPECTED_RECOMMENDED_FEATURE_GAPS, "recommendation feature gaps mismatch", issues)
    _require(recommendation.get("recommended_next_research_step") == EXPECTED_RECOMMENDED_NEXT_STEP, "recommendation research step mismatch", issues)
    _require(recommendation.get("high_priority_enrichment_gaps") == EXPECTED_RECOMMENDED_FEATURE_GAPS, "recommendation high priority gap mismatch", issues)

    _require(state.get("version") == EXPECTED_VERSION, "state version mismatch", issues)
    _require(state.get("previous_base") == EXPECTED_PREVIOUS_BASE, "state previous_base mismatch", issues)
    _require(state.get("final_verdict") == EXPECTED_FINAL_VERDICT, "state verdict mismatch", issues)
    _require(state.get("recommended_next_step") == EXPECTED_RECOMMENDED_NEXT_STEP, "state next step mismatch", issues)
    _require(state.get("recommended_data_enrichment_next") == EXPECTED_RECOMMENDED_DATA_ENRICHMENT, "state enrichment mismatch", issues)
    _require(state.get("recommended_feature_gaps_high_priority") == EXPECTED_RECOMMENDED_FEATURE_GAPS, "state feature gaps mismatch", issues)
    _require(state.get("project_state_aligned") is True, "state project_state_aligned must be true", issues)
    _require(state.get("latest_metrics_aligned") is True, "state latest_metrics_aligned must be true", issues)
    _require(state.get("latest_summary_aligned") is True, "state latest_summary_aligned must be true", issues)
    _require(state.get("all_json_values_finite") is True, "state all_json_values_finite must be true", issues)
    _require(state.get("recommendation_aligned") is True, "state recommendation_aligned must be true", issues)

    _require(latest_metrics.get("version") == EXPECTED_VERSION, "latest_metrics version mismatch", issues)
    _require(latest_metrics.get("previous_base") == EXPECTED_PREVIOUS_BASE, "latest_metrics previous_base mismatch", issues)
    _require(latest_metrics.get("final_verdict") == EXPECTED_FINAL_VERDICT, "latest_metrics verdict mismatch", issues)
    _require(latest_metrics.get("recommended_next_step") == EXPECTED_RECOMMENDED_NEXT_STEP, "latest_metrics next step mismatch", issues)
    _require(latest_metrics.get("recommended_data_enrichment_next") == EXPECTED_RECOMMENDED_DATA_ENRICHMENT, "latest_metrics enrichment mismatch", issues)
    _require(latest_metrics.get("recommended_feature_gaps_high_priority") == EXPECTED_RECOMMENDED_FEATURE_GAPS, "latest_metrics feature gaps mismatch", issues)
    _require(latest_metrics.get("project_state_aligned") is True, "latest_metrics project_state_aligned must be true", issues)
    _require(latest_metrics.get("latest_metrics_aligned") is True, "latest_metrics latest_metrics_aligned must be true", issues)
    _require(latest_metrics.get("latest_summary_aligned") is True, "latest_metrics latest_summary_aligned must be true", issues)
    _require(latest_metrics.get("all_json_values_finite") is True, "latest_metrics all_json_values_finite must be true", issues)
    _require(latest_metrics.get("recommendation_aligned") is True, "latest_metrics recommendation_aligned must be true", issues)

    if not args.allow_missing_release_reports:
        _require(release_report.get("version") == EXPECTED_VERSION, "release report version mismatch", issues)
        _require(release_report.get("release_ready_for_external_review") is True, "release report release_ready_for_external_review must be true", issues)
        _require(release_report.get("final_audit_passed") is True, "release report final_audit_passed must be true", issues)
        _require(release_report.get("final_smoke_passed") is True, "release report final_smoke_passed must be true", issues)

        _require(audit_report.get("forbidden_count") == 0, "audit forbidden_count must be 0", issues)
        _require(audit_report.get("missing_required_files") == [], "audit missing_required_files must be empty", issues)
        _require(audit_report.get("secret_hits") == [], "audit secret_hits must be empty", issues)
        _require(audit_report.get("clean_zip_ready_for_external_review") is True, "audit clean_zip_ready_for_external_review must be true", issues)

        _require(smoke_report.get("smoke_test_passed") is True, "smoke test must pass", issues)
        _require(smoke_report.get("codex_cli_called") is False, "smoke test codex_cli_called must be false", issues)
        _require(smoke_report.get("holdout_executed") is False, "smoke test holdout_executed must be false", issues)

    verdict = "VALIDATION PASSED" if not issues else "VALIDATION FAILED"
    print(verdict)
    if issues:
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
