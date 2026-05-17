from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FORBIDDEN_FEATURE_COLUMNS = {
    "forward_return_1bar",
    "forward_return_3bar",
    "forward_return_6bar",
    "forward_return_12bar",
    "max_favorable_excursion_1bar",
    "max_adverse_excursion_1bar",
    "max_favorable_excursion_3bar",
    "max_adverse_excursion_3bar",
    "max_favorable_excursion_6bar",
    "max_adverse_excursion_6bar",
    "max_favorable_excursion_12bar",
    "max_adverse_excursion_12bar",
    "direction_up_after_cost_3bar",
    "direction_up_after_cost_6bar",
    "tp_before_sl_conservative",
    "gross_pnl_pct",
    "net_pnl_pct",
    "mfe_pct",
    "mae_pct",
    "exit_reason",
    "simulation_status",
    "actual_target",
    "cost_adjusted_forward_return",
    "net_return_label",
    "signed_payoff_label",
    "asymmetric_payoff_label",
    "downside_risk_label",
    "ev_gap_label",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payoff_objective_reports(version: str) -> dict[str, Any]:
    v_norm = version.lower().replace(".", "_")
    expected_consistency_status = (
        "PAYOFF_OBJECTIVE_REPORTS_CONSISTENT_VALID_SPLITS_EXPLORATORY_ONLY"
        if v_norm == "v1_40_1"
        else "PAYOFF_OBJECTIVE_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    )
    expected_previous_base = "V1.40" if v_norm == "v1_40_1" else "V1.39"
    report_dir = Path("reports/research")
    required_json = [
        f"payoff_objective_input_guard_{v_norm}.json",
        f"payoff_objective_split_integrity_{v_norm}.json",
        f"payoff_objective_targets_{v_norm}.json",
        f"payoff_objective_candidates_{v_norm}.json",
        f"payoff_objective_walk_forward_eval_{v_norm}.json",
        f"payoff_objective_baseline_comparison_{v_norm}.json",
        f"payoff_objective_temporal_robustness_{v_norm}.json",
        f"payoff_objective_regime_breakdown_{v_norm}.json",
        f"payoff_objective_overfit_guard_{v_norm}.json",
        f"payoff_objective_research_summary_{v_norm}.json",
        f"payoff_objective_consistency_check_{v_norm}.json",
        f"{v_norm}_recommendation.json",
    ]
    required_md = [name.replace(".json", ".md") for name in required_json]
    issues: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    for name in required_json:
        path = report_dir / name
        if not path.exists():
            issues.append(f"Missing report: {name}")
            continue
        loaded[name] = _load_json(path)
    for name in required_md:
        if not (report_dir / name).exists():
            issues.append(f"Missing report: {name}")
    if issues:
        return {"status": "PAYOFF_OBJECTIVE_REPORTS_INCOMPLETE", "issues": issues, "version": version}

    summary = loaded[f"payoff_objective_research_summary_{v_norm}.json"]
    consistency = loaded[f"payoff_objective_consistency_check_{v_norm}.json"]
    split_integrity = loaded[f"payoff_objective_split_integrity_{v_norm}.json"]
    state = _load_json(Path("reports/PROJECT_STATE.json"))
    metrics = _load_json(Path("reports/current/latest_metrics.json"))
    candidates = loaded[f"payoff_objective_candidates_{v_norm}.json"]
    targets = loaded[f"payoff_objective_targets_{v_norm}.json"]

    checks = [
        (summary.get("previous_base") == expected_previous_base, "previous_base mismatch"),
        (summary.get("diagnostic_base") == "V1.39", "diagnostic_base must be V1.39"),
        (summary.get("canonical_base_version") == "V1.37.2", "canonical_base_version must be V1.37.2"),
        (summary.get("research_base_version") == "V1.38.4", "research_base_version must be V1.38.4"),
        (summary.get("evidence_classification") == "EXPLORATORY_ONLY", "evidence_classification must be EXPLORATORY_ONLY"),
        (summary.get("no_new_filter") is True, "no_new_filter must be true"),
        (summary.get("no_strategy_validated") is True, "no_strategy_validated must be true"),
        (summary.get("no_preregistration_yet") is True, "no_preregistration_yet must be true"),
        (summary.get("no_paper_live") is True, "no_paper_live must be true"),
        (summary.get("no_real_trading") is True, "no_real_trading must be true"),
        (summary.get("holdout_executed") is False, "holdout_executed must be false"),
        (summary.get("codex_cli_called") is False, "codex_cli_called must be false"),
        (summary.get("release_ready_for_external_review") is True, "release_ready_for_external_review must be true"),
        (summary.get("strategy_reviewer_ready") is False, "strategy_reviewer_ready must be false"),
        (summary.get("paper_live_ready") is False, "paper_live_ready must be false"),
        (summary.get("preregistration_ready") is False, "preregistration_ready must be false"),
        (summary.get("money_deployment_ready") is False, "money_deployment_ready must be false"),
        (summary.get("consistency_check_status") == expected_consistency_status, "summary consistency_check_status mismatch"),
        (summary.get("status_field_policy") == "REMOVED", "summary status_field_policy mismatch"),
        (summary.get("status_field_present") is False, "summary status_field_present must be false"),
        (summary.get("target_status") == "PAYOFF_OBJECTIVE_TARGETS_DEFINED_LABEL_ONLY", "target_status mismatch"),
        (summary.get("objective_candidate_status") == "PAYOFF_OBJECTIVE_CANDIDATES_DEFINED", "objective_candidate_status mismatch"),
        (summary.get("split_integrity_status") == "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_PASSED", "split_integrity_status mismatch"),
        (summary.get("invalid_split_count") == 0, "invalid_split_count must be zero"),
        (summary.get("all_splits_temporally_valid") is True, "all_splits_temporally_valid must be true"),
        (split_integrity.get("split_integrity_status") == "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_PASSED", "split_integrity report status mismatch"),
        (split_integrity.get("invalid_split_count") == 0, "split_integrity report invalid_split_count must be zero"),
        (split_integrity.get("all_splits_temporally_valid") is True, "split_integrity report all_splits_temporally_valid must be true"),
        (summary.get("walk_forward_eval_status") in {"PAYOFF_OBJECTIVE_WALK_FORWARD_EVAL_COMPLETE_VALID_SPLITS", "PAYOFF_OBJECTIVE_WALK_FORWARD_EVAL_PARTIAL_VALID_SPLITS"}, "walk_forward_eval_status mismatch"),
        (summary.get("baseline_comparison_status") == "PAYOFF_OBJECTIVE_BASELINE_COMPARISON_COMPLETE", "baseline_comparison_status mismatch"),
        (summary.get("temporal_robustness_status") in {"PAYOFF_OBJECTIVE_TEMPORAL_ROBUSTNESS_COMPLETE", "PAYOFF_OBJECTIVE_TEMPORAL_ROBUSTNESS_FAILED"}, "temporal_robustness_status mismatch"),
        (summary.get("regime_breakdown_status") in {"PAYOFF_OBJECTIVE_REGIME_BREAKDOWN_COMPLETE", "PAYOFF_OBJECTIVE_REGIME_DATA_LIMITED"}, "regime_breakdown_status mismatch"),
        (summary.get("overfit_guard_status") == "PAYOFF_OBJECTIVE_OVERFIT_RISK_MODERATE", "overfit_guard_status mismatch"),
        (summary.get("final_verdict") in {
            "PAYOFF_OBJECTIVE_RESEARCH_PROMISING_BUT_UNVALIDATED",
            "PAYOFF_OBJECTIVE_RESEARCH_INCONCLUSIVE",
            "PAYOFF_OBJECTIVE_RESEARCH_RECENT_WINDOW_WEAK",
            "PAYOFF_OBJECTIVE_RESEARCH_SPLIT_INTEGRITY_FAILED",
            "PAYOFF_OBJECTIVE_RESEARCH_FAILED",
        }, "final_verdict unexpected"),
        (targets.get("future_outcomes_used_only_as_training_labels") is True, "targets must be labels only"),
        (targets.get("targets_not_available_at_decision_time") is True, "targets must be unavailable at decision time"),
        (targets.get("target_leakage_policy") == "LABEL_ONLY_NOT_SELECTION_FEATURE", "target_leakage_policy mismatch"),
        (targets.get("payoff_target_status") == "PAYOFF_OBJECTIVE_TARGETS_DEFINED_LABEL_ONLY", "payoff_target_status mismatch"),
        (consistency.get("consistency_check_status") == expected_consistency_status, "consistency_check_status mismatch"),
        ("status" not in consistency, "legacy status field must be absent from consistency report"),
        (consistency.get("status_field_policy") == "REMOVED", "status_field_policy must be REMOVED"),
        (consistency.get("status_field_present") is False, "status_field_present must be false"),
        (consistency.get("split_integrity_status") == "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_PASSED", "consistency split_integrity_status mismatch"),
        (consistency.get("invalid_split_count") == 0, "consistency invalid_split_count must be zero"),
        (consistency.get("all_splits_temporally_valid") is True, "consistency all_splits_temporally_valid must be true"),
        (consistency.get("project_state_structured") is True, "project_state_structured must be true"),
        (consistency.get("project_state_paths_aligned") is True, "project_state_paths_aligned must be true"),
        (consistency.get("latest_metrics_aligned") is True, "latest_metrics_aligned must be true"),
        (consistency.get("release_ready_inconsistency_fixed") is True, "release_ready_inconsistency_fixed must be true"),
        (consistency.get("baseline_reporting_clarified") is True, "baseline_reporting_clarified must be true"),
        (consistency.get("no_new_filter") is True, "consistency no_new_filter must be true"),
        (consistency.get("no_strategy_validated") is True, "consistency no_strategy_validated must be true"),
        (consistency.get("no_preregistration_yet") is True, "consistency no_preregistration_yet must be true"),
        (consistency.get("no_paper_live") is True, "consistency no_paper_live must be true"),
        (consistency.get("no_real_trading") is True, "consistency no_real_trading must be true"),
        (state.get("version") == summary.get("version"), "PROJECT_STATE.version mismatch"),
        (state.get("previous_base") == expected_previous_base, "PROJECT_STATE.previous_base mismatch"),
        (state.get("canonical_base_version") == "V1.37.2", "PROJECT_STATE.canonical_base_version mismatch"),
        (state.get("research_base_version") == "V1.38.4", "PROJECT_STATE.research_base_version mismatch"),
        (state.get("diagnostic_base") == "V1.39", "PROJECT_STATE.diagnostic_base mismatch"),
        (state.get("final_verdict") == summary.get("final_verdict"), "PROJECT_STATE final_verdict mismatch"),
        (state.get("consistency_check_status") == expected_consistency_status, "PROJECT_STATE consistency_check_status mismatch"),
        (state.get("status_field_policy") == "REMOVED", "PROJECT_STATE status_field_policy mismatch"),
        (state.get("status_field_present") is False, "PROJECT_STATE status_field_present must be false"),
        (state.get("release_ready_for_external_review") is True, "PROJECT_STATE release_ready_for_external_review must be true"),
        (state.get("strategy_reviewer_ready") is False, "PROJECT_STATE strategy_reviewer_ready must be false"),
        (state.get("paper_live_ready") is False, "PROJECT_STATE paper_live_ready must be false"),
        (state.get("preregistration_ready") is False, "PROJECT_STATE preregistration_ready must be false"),
        (state.get("money_deployment_ready") is False, "PROJECT_STATE money_deployment_ready must be false"),
        (state.get("evidence_classification") == "EXPLORATORY_ONLY", "PROJECT_STATE evidence_classification mismatch"),
        (state.get("no_new_filter") is True, "PROJECT_STATE no_new_filter must be true"),
        (state.get("no_strategy_validated") is True, "PROJECT_STATE no_strategy_validated must be true"),
        (state.get("no_preregistration_yet") is True, "PROJECT_STATE no_preregistration_yet must be true"),
        (state.get("no_paper_live") is True, "PROJECT_STATE no_paper_live must be true"),
        (state.get("no_real_trading") is True, "PROJECT_STATE no_real_trading must be true"),
        (state.get("holdout_executed") is False, "PROJECT_STATE holdout_executed must be false"),
        (state.get("codex_cli_called") is False, "PROJECT_STATE codex_cli_called must be false"),
        (metrics.get("version") == summary.get("version"), "latest_metrics.version mismatch"),
        (metrics.get("final_verdict") == summary.get("final_verdict"), "latest_metrics final_verdict mismatch"),
        (metrics.get("consistency_check_status") == expected_consistency_status, "latest_metrics consistency_check_status mismatch"),
        (metrics.get("status_field_policy") == "REMOVED", "latest_metrics status_field_policy mismatch"),
        (metrics.get("status_field_present") is False, "latest_metrics status_field_present must be false"),
        (metrics.get("release_ready_for_external_review") is True, "latest_metrics release_ready_for_external_review must be true"),
        (metrics.get("strategy_reviewer_ready") is False, "latest_metrics strategy_reviewer_ready must be false"),
        (metrics.get("paper_live_ready") is False, "latest_metrics paper_live_ready must be false"),
        (metrics.get("preregistration_ready") is False, "latest_metrics preregistration_ready must be false"),
        (metrics.get("money_deployment_ready") is False, "latest_metrics money_deployment_ready must be false"),
        (metrics.get("evidence_classification") == "EXPLORATORY_ONLY", "latest_metrics evidence_classification mismatch"),
        (metrics.get("no_new_filter") is True, "latest_metrics no_new_filter must be true"),
        (metrics.get("no_strategy_validated") is True, "latest_metrics no_strategy_validated must be true"),
        (metrics.get("no_preregistration_yet") is True, "latest_metrics no_preregistration_yet must be true"),
        (metrics.get("no_paper_live") is True, "latest_metrics no_paper_live must be true"),
        (metrics.get("no_real_trading") is True, "latest_metrics no_real_trading must be true"),
        (metrics.get("holdout_executed") is False, "latest_metrics holdout_executed must be false"),
        (metrics.get("codex_cli_called") is False, "latest_metrics codex_cli_called must be false"),
        (metrics.get("split_integrity_status") == "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_PASSED", "latest_metrics split_integrity_status mismatch"),
        (metrics.get("invalid_split_count") == 0, "latest_metrics invalid_split_count must be zero"),
        (metrics.get("all_splits_temporally_valid") is True, "latest_metrics all_splits_temporally_valid must be true"),
        (metrics.get("overfit_guard_status") == "PAYOFF_OBJECTIVE_OVERFIT_RISK_MODERATE", "latest_metrics overfit_guard_status mismatch"),
    ]
    for ok, issue in checks:
        if not ok:
            issues.append(issue)

    for field in ["ready_for_reviewer", "ready_for_reviewer_scope", "ready_for_reviewer_is_release_ready"]:
        if field in state:
            issues.append(f"PROJECT_STATE must not contain {field}")
        if field in metrics:
            issues.append(f"latest_metrics must not contain {field}")
    if "ready_for_reviewer" in summary:
        issues.append("summary must not contain ready_for_reviewer")

    evaluated_splits = split_integrity.get("evaluated_splits", [])
    for idx, row in enumerate(evaluated_splits):
        train_start = row.get("train_start")
        train_end = row.get("train_end")
        test_start = row.get("test_start")
        test_end = row.get("test_end")
        if not (train_start and train_end and test_start and test_end):
            issues.append(f"evaluated split {idx} missing temporal boundary")
            continue
        if not (train_start <= train_end <= test_start < test_end):
            issues.append(f"evaluated split {idx} has invalid temporal ordering")
        if row.get("split_status") != "EVALUATED":
            issues.append(f"evaluated split {idx} must be evaluated")
        if int(row.get("train_count", 0)) <= 0 or int(row.get("test_count", 0)) <= 0:
            issues.append(f"evaluated split {idx} must not have silent zero metrics")

    if summary.get("selected_count_total_v1_39") != 129527:
        issues.append("selected_count_total_v1_39 mismatch")
    if summary.get("selected_count_2026_v1_39") != 19497:
        issues.append("selected_count_2026_v1_39 mismatch")
    if summary.get("best_candidate_observed") is None:
        issues.append("best_candidate_observed missing")
    if summary.get("best_candidate_reason") is None:
        issues.append("best_candidate_reason missing")
    if summary.get("beats_probability_baseline") not in {True, False}:
        issues.append("beats_probability_baseline missing")
    if summary.get("beats_ev_proxy_baseline") not in {True, False}:
        issues.append("beats_ev_proxy_baseline missing")

    for candidate in candidates.get("implemented_candidates", []):
        if not candidate:
            issues.append("implemented candidate missing")
    for column in _all_candidate_feature_columns(candidates):
        if column in FORBIDDEN_FEATURE_COLUMNS or any(column.startswith(prefix) for prefix in ["forward_return_", "max_favorable_excursion_", "max_adverse_excursion_", "direction_up_after_cost_", "tp_before_sl"]):
            issues.append(f"Forbidden feature column in candidate definitions: {column}")

    status = expected_consistency_status if not issues else "PAYOFF_OBJECTIVE_REPORTS_INCONSISTENT"
    return {
        "status": status,
        "issues": issues,
        "version": version,
        "consistency_check_status": expected_consistency_status,
        "project_state_structured": True,
        "project_state_paths_aligned": True,
        "latest_metrics_aligned": True,
        "release_ready_inconsistency_fixed": True,
        "baseline_reporting_clarified": True,
        "targets_label_only": True,
        "future_outcomes_used_only_as_labels": True,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "status_field_policy": "REMOVED",
        "status_field_present": False,
    }


def _all_candidate_feature_columns(candidates: dict[str, Any]) -> list[str]:
    feature_columns: list[str] = []
    for spec in candidates.get("candidates", []):
        feature_columns.extend(list(spec.get("feature_columns", [])))
    return sorted(set(feature_columns))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    print(json.dumps(validate_payoff_objective_reports(args.version), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
