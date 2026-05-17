from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


EXPECTED_CONSISTENCY_STATUS = "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _required_reports(version: str) -> list[Path]:
    v_norm = version.lower().replace(".", "_")
    report_dir = Path("reports/research")
    names = [
        f"payoff_objective_failure_input_guard_{v_norm}.json",
        f"payoff_objective_failure_input_guard_{v_norm}.md",
        f"payoff_candidate_rebuild_{v_norm}.json",
        f"payoff_candidate_rebuild_{v_norm}.md",
        f"payoff_score_decile_analysis_{v_norm}.json",
        f"payoff_score_decile_analysis_{v_norm}.md",
        f"payoff_label_noise_diagnostic_{v_norm}.json",
        f"payoff_label_noise_diagnostic_{v_norm}.md",
        f"payoff_downside_miss_analysis_{v_norm}.json",
        f"payoff_downside_miss_analysis_{v_norm}.md",
        f"payoff_feature_shift_2026_{v_norm}.json",
        f"payoff_feature_shift_2026_{v_norm}.md",
        f"payoff_regime_transfer_{v_norm}.json",
        f"payoff_regime_transfer_{v_norm}.md",
        f"payoff_cost_vs_gross_{v_norm}.json",
        f"payoff_cost_vs_gross_{v_norm}.md",
        f"payoff_ranking_quality_{v_norm}.json",
        f"payoff_ranking_quality_{v_norm}.md",
        f"payoff_objective_failure_diagnostic_summary_{v_norm}.json",
        f"payoff_objective_failure_diagnostic_summary_{v_norm}.md",
        f"payoff_objective_failure_consistency_check_{v_norm}.json",
        f"payoff_objective_failure_consistency_check_{v_norm}.md",
        f"v1_41_recommendation.json",
        f"v1_41_recommendation.md",
    ]
    return [report_dir / name for name in names]


def _issue(issues: list[str], ok: bool, message: str) -> None:
    if not ok:
        issues.append(message)


def validate_payoff_objective_failure_diagnostic_reports(version: str) -> dict[str, Any]:
    v_norm = version.lower().replace(".", "_")
    issues: list[str] = []
    paths = _required_reports(version)
    loaded: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.exists():
            issues.append(f"Missing report: {path.name}")
            continue
        if path.suffix == ".json":
            loaded[path.name] = _load_json(path)

    if issues:
        return {
            "status": "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_INCOMPLETE",
            "version": version.upper(),
            "issues": issues,
        }

    summary = loaded[f"payoff_objective_failure_diagnostic_summary_{v_norm}.json"]
    consistency = loaded[f"payoff_objective_failure_consistency_check_{v_norm}.json"]
    input_guard = loaded[f"payoff_objective_failure_input_guard_{v_norm}.json"]
    candidate_rebuild = loaded[f"payoff_candidate_rebuild_{v_norm}.json"]
    score_decile = loaded[f"payoff_score_decile_analysis_{v_norm}.json"]

    state = _load_json(Path("reports/PROJECT_STATE.json"))
    metrics = _load_json(Path("reports/current/latest_metrics.json"))

    _issue(issues, summary.get("version") == "V1.41", "version mismatch")
    _issue(issues, summary.get("payoff_objective_base_version") == "V1.40.1", "payoff_objective_base_version must be V1.40.1")
    _issue(issues, summary.get("diagnostic_base") == "V1.39", "diagnostic_base must be V1.39")
    _issue(issues, summary.get("canonical_base_version") == "V1.37.2", "canonical_base_version must be V1.37.2")
    _issue(issues, summary.get("research_base_version") == "V1.38.4", "research_base_version must be V1.38.4")
    _issue(issues, summary.get("candidate") == "asymmetric_loss_weighted_classifier", "candidate must be asymmetric_loss_weighted_classifier")
    _issue(
        issues,
        summary.get("candidate_rebuild_status") == "PAYOFF_OBJECTIVE_CANDIDATE_REBUILD_MATCH",
        "candidate_rebuild_status must be PAYOFF_OBJECTIVE_CANDIDATE_REBUILD_MATCH",
    )
    _issue(issues, summary.get("selected_filter") == "filter_ev_gt_0", "selected_filter must be filter_ev_gt_0")
    _issue(issues, summary.get("best_candidate_observed") == "asymmetric_loss_weighted_classifier", "best_candidate_observed mismatch")
    _issue(issues, summary.get("metric_match_v1_40_1") is True, "metric_match_v1_40_1 must be true")
    _issue(issues, summary.get("downside_match_v1_40_1") is True, "downside_match_v1_40_1 must be true")
    _issue(issues, summary.get("selected_filter") == "filter_ev_gt_0", "selected_filter must be filter_ev_gt_0")
    _issue(issues, int(summary.get("selected_count_total", -1)) == 129527, "selected_count_total mismatch")
    _issue(issues, int(summary.get("selected_count_2026", -1)) == 19497, "selected_count_2026 mismatch")
    _issue(issues, float(summary.get("best_candidate_2026_metric", 0.0)) == -0.004918998589848299, "best_candidate_2026_metric mismatch")
    _issue(issues, float(summary.get("best_candidate_downside_metric", 0.0)) == 0.5385878489326765, "best_candidate_downside_metric mismatch")
    _issue(issues, summary.get("recent_window_status") == "RECENT_WINDOW_WEAK", "recent_window_status mismatch")
    _issue(issues, summary.get("final_verdict") == "PAYOFF_OBJECTIVE_FAILURE_MULTI_FACTOR", "final_verdict mismatch")
    _issue(issues, summary.get("evidence_classification") == "DIAGNOSTIC_ONLY", "evidence_classification must be DIAGNOSTIC_ONLY")
    _issue(issues, summary.get("no_new_filter") is True, "no_new_filter must be true")
    _issue(issues, summary.get("no_strategy_validated") is True, "no_strategy_validated must be true")
    _issue(issues, summary.get("no_preregistration_yet") is True, "no_preregistration_yet must be true")
    _issue(issues, summary.get("no_paper_live") is True, "no_paper_live must be true")
    _issue(issues, summary.get("no_real_trading") is True, "no_real_trading must be true")
    _issue(issues, summary.get("holdout_executed") is False, "holdout_executed must be false")
    _issue(issues, summary.get("codex_cli_called") is False, "codex_cli_called must be false")
    _issue(issues, summary.get("release_ready_for_external_review") is True, "release_ready_for_external_review must be true")
    _issue(issues, summary.get("strategy_reviewer_ready") is False, "strategy_reviewer_ready must be false")
    _issue(issues, summary.get("paper_live_ready") is False, "paper_live_ready must be false")
    _issue(issues, summary.get("preregistration_ready") is False, "preregistration_ready must be false")
    _issue(issues, summary.get("money_deployment_ready") is False, "money_deployment_ready must be false")
    _issue(
        issues,
        summary.get("consistency_check_status") == EXPECTED_CONSISTENCY_STATUS,
        "summary consistency_check_status mismatch",
    )
    _issue(issues, summary.get("status_field_policy") == "REMOVED", "summary status_field_policy must be REMOVED")
    _issue(issues, summary.get("status_field_present") is False, "summary status_field_present must be false")
    _issue(
        issues,
        summary.get("status_field_matches_consistency_check_status") is True,
        "summary status_field_matches_consistency_check_status must be true",
    )
    _issue(
        issues,
        summary.get("ambiguous_ready_for_reviewer_removed") is True,
        "summary ambiguous_ready_for_reviewer_removed must be true",
    )
    _issue(issues, "ready_for_reviewer" not in summary, "summary must not contain ready_for_reviewer")
    _issue(
        issues,
        summary.get("overfit_guard_status") == "PAYOFF_OBJECTIVE_OVERFIT_RISK_MODERATE",
        "summary overfit_guard_status must be PAYOFF_OBJECTIVE_OVERFIT_RISK_MODERATE",
    )
    _issue(
        issues,
        input_guard.get("failure_input_guard_status") == "PAYOFF_OBJECTIVE_FAILURE_INPUT_GUARD_PASSED",
        "input_guard failure status mismatch",
    )
    _issue(
        issues,
        input_guard.get("payoff_objective_base_version") == "V1.40.1",
        "input_guard payoff_objective_base_version mismatch",
    )
    _issue(
        issues,
        input_guard.get("diagnostic_base") == "V1.39",
        "input_guard diagnostic_base mismatch",
    )
    _issue(
        issues,
        input_guard.get("canonical_base_version") == "V1.37.2",
        "input_guard canonical_base_version mismatch",
    )
    _issue(
        issues,
        input_guard.get("research_base_version") == "V1.38.4",
        "input_guard research_base_version mismatch",
    )
    _issue(
        issues,
        int(input_guard.get("raw_prediction_rows", -1)) == 171648,
        "input_guard raw_prediction_rows mismatch",
    )
    _issue(
        issues,
        int(input_guard.get("selected_count_total_v1_39", -1)) == 129527,
        "input_guard selected_count_total_v1_39 mismatch",
    )
    _issue(
        issues,
        int(input_guard.get("selected_count_2026_v1_39", -1)) == 19497,
        "input_guard selected_count_2026_v1_39 mismatch",
    )
    _issue(
        issues,
        input_guard.get("best_candidate_observed") == "asymmetric_loss_weighted_classifier",
        "input_guard best_candidate_observed mismatch",
    )
    _issue(
        issues,
        input_guard.get("recent_window_status") == "RECENT_WINDOW_WEAK",
        "input_guard recent_window_status mismatch",
    )
    _issue(
        issues,
        input_guard.get("final_verdict") == "PAYOFF_OBJECTIVE_RESEARCH_RECENT_WINDOW_WEAK",
        "input_guard final_verdict mismatch",
    )
    _issue(
        issues,
        score_decile.get("score_decile_status") in {
            "SCORE_DECILES_NON_MONOTONIC_2026",
            "SCORE_DECILES_WEAK_BUT_ORDERED",
            "SCORE_DECILES_DIAGNOSTIC_INCONCLUSIVE",
        },
        "score_decile_status unexpected",
    )
    _issue(issues, "status" not in consistency, "legacy status field must be absent")
    _issue(
        issues,
        consistency.get("consistency_check_status") == EXPECTED_CONSISTENCY_STATUS,
        "consistency consistency_check_status mismatch",
    )
    _issue(
        issues,
        consistency.get("status_field_policy") == "REMOVED",
        "consistency status_field_policy must be REMOVED",
    )
    _issue(
        issues,
        consistency.get("status_field_present") is False,
        "consistency status_field_present must be false",
    )
    _issue(
        issues,
        consistency.get("status_field_matches_consistency_check_status") is True,
        "consistency status_field_matches_consistency_check_status must be true",
    )
    _issue(
        issues,
        consistency.get("ambiguous_ready_for_reviewer_removed") is True,
        "consistency ambiguous_ready_for_reviewer_removed must be true",
    )
    _issue(
        issues,
        consistency.get("project_state_structured") is True,
        "consistency project_state_structured must be true",
    )
    _issue(
        issues,
        consistency.get("project_state_paths_aligned") is True,
        "consistency project_state_paths_aligned must be true",
    )
    _issue(
        issues,
        consistency.get("latest_metrics_aligned") is True,
        "consistency latest_metrics_aligned must be true",
    )
    _issue(
        issues,
        consistency.get("release_ready_inconsistency_fixed") is True,
        "consistency release_ready_inconsistency_fixed must be true",
    )
    _issue(
        issues,
        consistency.get("baseline_reporting_clarified") is True,
        "consistency baseline_reporting_clarified must be true",
    )
    _issue(
        issues,
        consistency.get("reviewer_readiness_semantics_clarified") is True,
        "consistency reviewer_readiness_semantics_clarified must be true",
    )
    _issue(
        issues,
        consistency.get("no_strategy_validated") is True,
        "consistency no_strategy_validated must be true",
    )
    _issue(
        issues,
        consistency.get("no_paper_live") is True,
        "consistency no_paper_live must be true",
    )
    _issue(
        issues,
        consistency.get("no_real_trading") is True,
        "consistency no_real_trading must be true",
    )
    _issue(issues, consistency.get("issues_found") == [], "consistency issues_found must be empty")

    for field in ["ready_for_reviewer", "ready_for_reviewer_scope", "ready_for_reviewer_is_release_ready"]:
        _issue(issues, field not in state, f"PROJECT_STATE must not contain {field}")
        _issue(issues, field not in metrics, f"latest_metrics must not contain {field}")

    _issue(issues, state.get("version") == "V1.41", "PROJECT_STATE version mismatch")
    _issue(issues, state.get("previous_base") == "V1.40.1", "PROJECT_STATE previous_base mismatch")
    _issue(issues, state.get("payoff_objective_base_version") == "V1.40.1", "PROJECT_STATE payoff_objective_base_version mismatch")
    _issue(issues, state.get("diagnostic_base") == "V1.39", "PROJECT_STATE diagnostic_base mismatch")
    _issue(issues, state.get("canonical_base_version") == "V1.37.2", "PROJECT_STATE canonical_base_version mismatch")
    _issue(issues, state.get("research_base_version") == "V1.38.4", "PROJECT_STATE research_base_version mismatch")
    _issue(issues, state.get("purpose") == "payoff-aware objective 2026 failure diagnostic", "PROJECT_STATE purpose mismatch")
    _issue(issues, state.get("selected_filter") == "filter_ev_gt_0", "PROJECT_STATE selected_filter mismatch")
    _issue(issues, state.get("best_candidate_observed") == "asymmetric_loss_weighted_classifier", "PROJECT_STATE best_candidate_observed mismatch")
    _issue(issues, int(state.get("selected_count_total", -1)) == 129527, "PROJECT_STATE selected_count_total mismatch")
    _issue(issues, int(state.get("selected_count_2026", -1)) == 19497, "PROJECT_STATE selected_count_2026 mismatch")
    _issue(issues, float(state.get("best_candidate_2026_metric", 0.0)) == -0.004918998589848299, "PROJECT_STATE best_candidate_2026_metric mismatch")
    _issue(issues, float(state.get("best_candidate_downside_metric", 0.0)) == 0.5385878489326765, "PROJECT_STATE best_candidate_downside_metric mismatch")
    _issue(issues, state.get("final_verdict") == "PAYOFF_OBJECTIVE_FAILURE_MULTI_FACTOR", "PROJECT_STATE final_verdict mismatch")
    _issue(issues, state.get("consistency_check_status") == EXPECTED_CONSISTENCY_STATUS, "PROJECT_STATE consistency_check_status mismatch")
    _issue(issues, state.get("status_field_policy") == "REMOVED", "PROJECT_STATE status_field_policy mismatch")
    _issue(issues, state.get("status_field_present") is False, "PROJECT_STATE status_field_present must be false")
    _issue(issues, state.get("release_ready_for_external_review") is True, "PROJECT_STATE release_ready_for_external_review must be true")
    _issue(issues, state.get("strategy_reviewer_ready") is False, "PROJECT_STATE strategy_reviewer_ready must be false")
    _issue(issues, state.get("paper_live_ready") is False, "PROJECT_STATE paper_live_ready must be false")
    _issue(issues, state.get("preregistration_ready") is False, "PROJECT_STATE preregistration_ready must be false")
    _issue(issues, state.get("money_deployment_ready") is False, "PROJECT_STATE money_deployment_ready must be false")
    _issue(issues, state.get("evidence_classification") == "DIAGNOSTIC_ONLY", "PROJECT_STATE evidence_classification mismatch")
    _issue(issues, state.get("no_new_filter") is True, "PROJECT_STATE no_new_filter must be true")
    _issue(issues, state.get("no_strategy_validated") is True, "PROJECT_STATE no_strategy_validated must be true")
    _issue(issues, state.get("no_preregistration_yet") is True, "PROJECT_STATE no_preregistration_yet must be true")
    _issue(issues, state.get("no_paper_live") is True, "PROJECT_STATE no_paper_live must be true")
    _issue(issues, state.get("no_real_trading") is True, "PROJECT_STATE no_real_trading must be true")
    _issue(issues, state.get("holdout_executed") is False, "PROJECT_STATE holdout_executed must be false")
    _issue(issues, state.get("codex_cli_called") is False, "PROJECT_STATE codex_cli_called must be false")
    _issue(issues, state.get("overfit_guard_status") == "PAYOFF_OBJECTIVE_OVERFIT_RISK_MODERATE", "PROJECT_STATE overfit_guard_status mismatch")

    _issue(issues, metrics.get("version") == "V1.41", "latest_metrics version mismatch")
    _issue(issues, metrics.get("payoff_objective_base_version") == "V1.40.1", "latest_metrics payoff_objective_base_version mismatch")
    _issue(issues, metrics.get("selected_filter") == "filter_ev_gt_0", "latest_metrics selected_filter mismatch")
    _issue(issues, metrics.get("best_candidate_observed") == "asymmetric_loss_weighted_classifier", "latest_metrics best_candidate_observed mismatch")
    _issue(issues, int(metrics.get("selected_count_total", -1)) == 129527, "latest_metrics selected_count_total mismatch")
    _issue(issues, int(metrics.get("selected_count_2026", -1)) == 19497, "latest_metrics selected_count_2026 mismatch")
    _issue(issues, float(metrics.get("best_candidate_2026_metric", 0.0)) == -0.004918998589848299, "latest_metrics best_candidate_2026_metric mismatch")
    _issue(issues, float(metrics.get("best_candidate_downside_metric", 0.0)) == 0.5385878489326765, "latest_metrics best_candidate_downside_metric mismatch")
    _issue(issues, metrics.get("final_verdict") == "PAYOFF_OBJECTIVE_FAILURE_MULTI_FACTOR", "latest_metrics final_verdict mismatch")
    _issue(issues, metrics.get("consistency_check_status") == EXPECTED_CONSISTENCY_STATUS, "latest_metrics consistency_check_status mismatch")
    _issue(issues, metrics.get("status_field_policy") == "REMOVED", "latest_metrics status_field_policy mismatch")
    _issue(issues, metrics.get("status_field_present") is False, "latest_metrics status_field_present must be false")
    _issue(issues, metrics.get("release_ready_for_external_review") is True, "latest_metrics release_ready_for_external_review must be true")
    _issue(issues, metrics.get("strategy_reviewer_ready") is False, "latest_metrics strategy_reviewer_ready must be false")
    _issue(issues, metrics.get("paper_live_ready") is False, "latest_metrics paper_live_ready must be false")
    _issue(issues, metrics.get("preregistration_ready") is False, "latest_metrics preregistration_ready must be false")
    _issue(issues, metrics.get("money_deployment_ready") is False, "latest_metrics money_deployment_ready must be false")
    _issue(issues, metrics.get("evidence_classification") == "DIAGNOSTIC_ONLY", "latest_metrics evidence_classification mismatch")
    _issue(issues, metrics.get("no_new_filter") is True, "latest_metrics no_new_filter must be true")
    _issue(issues, metrics.get("no_strategy_validated") is True, "latest_metrics no_strategy_validated must be true")
    _issue(issues, metrics.get("no_preregistration_yet") is True, "latest_metrics no_preregistration_yet must be true")
    _issue(issues, metrics.get("no_paper_live") is True, "latest_metrics no_paper_live must be true")
    _issue(issues, metrics.get("no_real_trading") is True, "latest_metrics no_real_trading must be true")
    _issue(issues, metrics.get("holdout_executed") is False, "latest_metrics holdout_executed must be false")
    _issue(issues, metrics.get("codex_cli_called") is False, "latest_metrics codex_cli_called must be false")
    _issue(issues, metrics.get("overfit_guard_status") == "PAYOFF_OBJECTIVE_OVERFIT_RISK_MODERATE", "latest_metrics overfit_guard_status mismatch")

    for split in summary.get("split_integrity", {}).get("evaluated_splits", []):
        train_start = pd.Timestamp(split.get("train_start"))
        train_end = pd.Timestamp(split.get("train_end"))
        test_start = pd.Timestamp(split.get("test_start"))
        test_end = pd.Timestamp(split.get("test_end"))
        _issue(issues, train_start <= train_end <= test_start < test_end, f"invalid temporal ordering for split {split.get('name')}")
        _issue(issues, int(split.get("train_count", 0)) > 0, f"split {split.get('name')} must have positive train_count")
        _issue(issues, int(split.get("test_count", 0)) > 0, f"split {split.get('name')} must have positive test_count")

    return {
        "version": "V1.41",
        "status": EXPECTED_CONSISTENCY_STATUS if not issues else "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_INCONSISTENT",
        "consistency_check_status": EXPECTED_CONSISTENCY_STATUS,
        "issues": issues,
        "release_ready_for_external_review": True,
        "strategy_reviewer_ready": False,
        "paper_live_ready": False,
        "preregistration_ready": False,
        "money_deployment_ready": False,
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    print(json.dumps(validate_payoff_objective_failure_diagnostic_reports(args.version), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
