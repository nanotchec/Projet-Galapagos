from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _normalize_version(version: str) -> str:
    v = version.lower()
    if not v.startswith("v"):
        v = "v" + v
    return v.replace(".", "_")


def _load_json(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def _load_report(report_dir: str, version_suffix: str, key: str) -> tuple[Path, dict[str, Any] | None]:
    base_name = f"{version_suffix}_{key}" if key == "recommendation" else f"{key}_{version_suffix}"
    path = Path(report_dir) / f"{base_name}.json"
    if not path.exists():
        return path, None
    return path, _load_json(path)


def _validate_v138(version: str, report_dir: str) -> dict[str, Any]:
    v_suffix = _normalize_version(version)
    required_keys = [
        "ev_net_canonical_input_guard",
        "ev_net_feature_rebuild",
        "ev_net_filter_grid",
        "ev_net_filter_evaluation",
        "ev_net_random_baselines",
        "ev_net_temporal_robustness",
        "ev_net_regime_robustness",
        "ev_net_overfit_guard",
        "ev_net_research_summary",
        "ev_net_research_consistency_check",
        "recommendation",
    ]

    issues: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for key in required_keys:
        path, payload = _load_report(report_dir, v_suffix, key)
        if payload is None:
            missing.append(str(path))
            continue
        loaded[key] = payload

    if missing:
        return {"status": "EV_NET_CANONICAL_RESEARCH_REPORTS_INCOMPLETE", "issues": [f"Missing required report: {p}" for p in missing], "version": version}

    summary = loaded["ev_net_research_summary"]
    guard = loaded["ev_net_canonical_input_guard"]
    rebuild = loaded["ev_net_feature_rebuild"]
    grid = loaded["ev_net_filter_grid"]
    evaluation = loaded["ev_net_filter_evaluation"]
    recs = loaded["recommendation"]
    consistency = loaded["ev_net_research_consistency_check"]
    overfit = loaded["ev_net_overfit_guard"]

    if guard.get("canonical_base_version") != "V1.37.2":
        issues.append("canonical_base_version must be V1.37.2")
    if guard.get("guard_status") != "EV_NET_CANONICAL_INPUT_GUARD_PASSED":
        issues.append(f"input guard failed: {guard.get('guard_status')}")
    if guard.get("real_data_enforced") is not True:
        issues.append("real_data_enforced must be true")
    if guard.get("mock_data_detected"):
        issues.append("mock_data_detected must be false")
    for field in ["raw_prediction_rows", "selection_dataset_rows", "outcome_dataset_rows", "opportunity_index_rows"]:
        if int(guard.get(field, 0)) != 171648:
            issues.append(f"{field} must be 171648")
    if int(guard.get("raw_prediction_rows_2026", 0)) != 24360:
        issues.append("raw_prediction_rows_2026 must be 24360")

    if rebuild.get("selection_outcome_split_status") != "PREDICTION_FRAME_INTEGRITY_PASSED":
        issues.append("selection/outcome split must be used with integrity passed")
    if rebuild.get("selection_frame_forbidden_columns"):
        issues.append("Forbidden outcome columns leaked into selection frame")
    if rebuild.get("default_payoff_used") is True:
        issues.append("default_payoff_used must be false")
    if rebuild.get("fallback_probability_used") is True:
        issues.append("fallback_probability_used must be false")
    if rebuild.get("artificial_probability_threshold_used") is True:
        issues.append("artificial_probability_threshold_used must be false")

    if grid.get("non_causal_filter_count", 0) < 1:
        issues.append("Expected at least one excluded non-causal filter")
    eligible_filters = set(grid.get("eligible_filters", []))
    excluded_filters = set(grid.get("excluded_filters", []))
    if "filter_ev_top_quantile_non_causal" not in excluded_filters:
        issues.append("Non-causal filter must be excluded from ranking")
    for item in evaluation.get("results", []):
        if item.get("filter_name") not in eligible_filters:
            issues.append(f"Non-eligible filter present in evaluation: {item.get('filter_name')}")

    if summary.get("evidence_classification") != "EXPLORATORY_ONLY":
        issues.append("evidence_classification must be EXPLORATORY_ONLY")
    if overfit.get("evidence_classification") != "EXPLORATORY_ONLY":
        issues.append("Overfit guard must remain exploratory-only")
    if overfit.get("preregistration_allowed") is not False:
        issues.append("Overfit guard preregistration_allowed must be false")
    if overfit.get("paper_live_allowed") is not False:
        issues.append("Overfit guard paper_live_allowed must be false")
    for field in ["no_strategy_validated", "no_preregistration_yet", "no_paper_live", "no_real_trading"]:
        if summary.get(field) is not True:
            issues.append(f"{field} must be true")
    if summary.get("holdout_executed") is not False:
        issues.append("holdout_executed must be false")
    if summary.get("codex_cli_called") is not False:
        issues.append("codex_cli_called must be false")
    if summary.get("final_verdict") != recs.get("final_verdict"):
        issues.append("Summary and recommendation final_verdict mismatch")
    if summary.get("consistency_check_status") != "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY":
        issues.append("consistency_check_status must be EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY")
    if consistency.get("status") != "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY":
        issues.append(f"Consistency report status mismatch: {consistency.get('status')}")

    report_root = Path(report_dir).resolve().parent
    state_path = report_root / "PROJECT_STATE.json"
    metrics_path = report_root / "current" / "latest_metrics.json"
    if not state_path.exists():
        issues.append(f"Missing PROJECT_STATE: {state_path}")
    if not metrics_path.exists():
        issues.append(f"Missing latest metrics: {metrics_path}")
    if state_path.exists():
        state = _load_json(state_path)
        for field in [
            "version",
            "canonical_base_version",
            "input_guard_status",
            "ev_feature_rebuild_status",
            "filter_grid_status",
            "evaluation_status",
            "random_baseline_status",
            "temporal_robustness_status",
            "regime_robustness_status",
            "overfit_guard_status",
            "best_filter_observed",
            "best_filter_selected_count",
            "best_filter_selected_count_2026",
            "best_filter_mean_net_pnl",
            "best_filter_2026_mean_net_pnl",
            "beats_monthly_random_p95",
            "final_verdict",
            "recommended_next_step",
            "evidence_classification",
            "no_strategy_validated",
            "no_preregistration_yet",
            "no_paper_live",
            "no_real_trading",
            "holdout_executed",
            "codex_cli_called",
        ]:
            if state.get(field) != summary.get(field):
                issues.append(f"PROJECT_STATE mismatch on {field}")
    if metrics_path.exists():
        metrics = _load_json(metrics_path)
        metric_fields = [
            "version",
            "canonical_base_version",
            "input_guard_status",
            "ev_feature_rebuild_status",
            "filter_grid_status",
            "evaluation_status",
            "random_baseline_status",
            "temporal_robustness_status",
            "regime_robustness_status",
            "overfit_guard_status",
            "best_filter_observed",
            "best_filter_selected_count",
            "best_filter_selected_count_2026",
            "best_filter_mean_net_pnl",
            "best_filter_2026_mean_net_pnl",
            "beats_monthly_random_p95",
            "final_verdict",
            "recommended_next_step",
            "evidence_classification",
            "no_strategy_validated",
            "no_preregistration_yet",
            "no_paper_live",
            "no_real_trading",
            "holdout_executed",
            "codex_cli_called",
        ]
        for field in metric_fields:
            if metrics.get(field) != summary.get(field):
                issues.append(f"latest_metrics mismatch on {field}")

    status = (
        "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
        if not issues
        else "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    )
    return {
        "status": status,
        "issues": issues,
        "version": version,
    }


def _validate_v1381(version: str, report_dir: str) -> dict[str, Any]:
    v_suffix = _normalize_version(version)
    required_keys = [
        "ev_net_canonical_input_guard",
        "ev_net_feature_rebuild",
        "ev_net_filter_grid",
        "ev_net_filter_evaluation",
        "ev_net_random_baselines",
        "ev_net_temporal_robustness",
        "ev_net_regime_robustness",
        "ev_net_overfit_guard",
        "ev_net_baseline_interpretation",
        "ev_net_research_summary",
        "ev_net_research_consistency_check",
        "recommendation",
    ]

    issues: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for key in required_keys:
        path, payload = _load_report(report_dir, v_suffix, key)
        if payload is None:
            missing.append(str(path))
            continue
        loaded[key] = payload

    if missing:
        return {
            "status": "EV_NET_CANONICAL_RESEARCH_REPORTS_INCOMPLETE",
            "issues": [f"Missing required report: {p}" for p in missing],
            "version": version,
        }

    summary = loaded["ev_net_research_summary"]
    guard = loaded["ev_net_canonical_input_guard"]
    rebuild = loaded["ev_net_feature_rebuild"]
    grid = loaded["ev_net_filter_grid"]
    evaluation = loaded["ev_net_filter_evaluation"]
    recs = loaded["recommendation"]
    consistency = loaded["ev_net_research_consistency_check"]
    overfit = loaded["ev_net_overfit_guard"]
    baseline_interp = loaded["ev_net_baseline_interpretation"]

    if guard.get("canonical_base_version") != "V1.37.2":
        issues.append("canonical_base_version must be V1.37.2")
    if guard.get("guard_status") != "EV_NET_CANONICAL_INPUT_GUARD_PASSED":
        issues.append(f"input guard failed: {guard.get('guard_status')}")
    if guard.get("real_data_enforced") is not True:
        issues.append("real_data_enforced must be true")
    if guard.get("mock_data_detected"):
        issues.append("mock_data_detected must be false")
    for field in ["raw_prediction_rows", "selection_dataset_rows", "outcome_dataset_rows", "opportunity_index_rows"]:
        if int(guard.get(field, 0)) != 171648:
            issues.append(f"{field} must be 171648")
    if int(guard.get("raw_prediction_rows_2026", 0)) != 24360:
        issues.append("raw_prediction_rows_2026 must be 24360")

    if rebuild.get("selection_outcome_split_status") != "PREDICTION_FRAME_INTEGRITY_PASSED":
        issues.append("selection/outcome split must be used with integrity passed")
    if rebuild.get("selection_frame_forbidden_columns"):
        issues.append("Forbidden outcome columns leaked into selection frame")
    if rebuild.get("default_payoff_used") is True:
        issues.append("default_payoff_used must be false")
    if rebuild.get("fallback_probability_used") is True:
        issues.append("fallback_probability_used must be false")
    if rebuild.get("artificial_probability_threshold_used") is True:
        issues.append("artificial_probability_threshold_used must be false")

    if grid.get("non_causal_filter_count", 0) < 1:
        issues.append("Expected at least one excluded non-causal filter")
    eligible_filters = set(grid.get("eligible_filters", []))
    excluded_filters = set(grid.get("excluded_filters", []))
    if "filter_ev_top_quantile_non_causal" not in excluded_filters:
        issues.append("Non-causal filter must be excluded from ranking")
    for item in evaluation.get("results", []):
        if item.get("filter_name") not in eligible_filters:
            issues.append(f"Non-eligible filter present in evaluation: {item.get('filter_name')}")

    if summary.get("evidence_classification") != "EXPLORATORY_ONLY":
        issues.append("evidence_classification must be EXPLORATORY_ONLY")
    if overfit.get("evidence_classification") != "EXPLORATORY_ONLY":
        issues.append("Overfit guard must remain exploratory-only")
    if overfit.get("preregistration_allowed") is not False:
        issues.append("Overfit guard preregistration_allowed must be false")
    if overfit.get("paper_live_allowed") is not False:
        issues.append("Overfit guard paper_live_allowed must be false")
    for field in ["no_strategy_validated", "no_preregistration_yet", "no_paper_live", "no_real_trading"]:
        if summary.get(field) is not True:
            issues.append(f"{field} must be true")
    if summary.get("holdout_executed") is not False:
        issues.append("holdout_executed must be false")
    if summary.get("codex_cli_called") is not False:
        issues.append("codex_cli_called must be false")

    if summary.get("baseline_reporting_status") != "EV_NET_BASELINE_REPORTING_CLARIFIED":
        issues.append("baseline_reporting_status must be EV_NET_BASELINE_REPORTING_CLARIFIED")
    if not isinstance(summary.get("project_state_structured"), bool) or summary.get("project_state_structured") is not True:
        issues.append("project_state_structured must be true")
    if summary.get("release_ready_for_external_review") is not True:
        issues.append("release_ready_for_external_review must be true")
    if summary.get("previous_v1_38_release_ready_inconsistency_fixed") is not True:
        issues.append("previous_v1_38_release_ready_inconsistency_fixed must be true")
    if summary.get("recommendation_artifact_json_path") != "reports/research/v1_38_1_recommendation.json":
        issues.append("recommendation_artifact_json_path must point to v1_38_1 recommendation")
    if summary.get("recommendation_artifact_md_path") != "reports/research/v1_38_1_recommendation.md":
        issues.append("recommendation_artifact_md_path must point to v1_38_1 recommendation")

    for field in [
        "beats_global_random_p95",
        "beats_monthly_random_p95",
        "top_global_pnl_filter",
        "top_global_pnl_filter_recent_2026_selected_count",
        "top_global_pnl_filter_recent_status",
    ]:
        if field not in summary:
            issues.append(f"Missing summary field: {field}")

    if summary.get("top_global_pnl_filter") != "filter_ev_top_quantile_causal":
        issues.append("top_global_pnl_filter must be filter_ev_top_quantile_causal")
    if summary.get("top_global_pnl_filter_recent_2026_selected_count") != 0:
        issues.append("top_global_pnl_filter_recent_2026_selected_count must be 0")
    if summary.get("top_global_pnl_filter_recent_status") != "RECENT_WINDOW_NO_SIGNALS":
        issues.append("top_global_pnl_filter_recent_status must be RECENT_WINDOW_NO_SIGNALS")

    if baseline_interp.get("baseline_reporting_status") != "EV_NET_BASELINE_REPORTING_CLARIFIED":
        issues.append("Baseline interpretation report status mismatch")
    if baseline_interp.get("top_global_pnl_filter") != "filter_ev_top_quantile_causal":
        issues.append("Baseline interpretation top_global_pnl_filter mismatch")
    if baseline_interp.get("top_global_pnl_filter_recent_2026_selected_count") != 0:
        issues.append("Baseline interpretation recent 2026 selected count mismatch")
    if baseline_interp.get("top_global_pnl_filter_recent_status") != "RECENT_WINDOW_NO_SIGNALS":
        issues.append("Baseline interpretation recent status mismatch")
    if baseline_interp.get("beats_global_random_p95") is not False:
        issues.append("Baseline interpretation beats_global_random_p95 must be false")
    if baseline_interp.get("beats_monthly_random_p95") is not True:
        issues.append("Baseline interpretation beats_monthly_random_p95 must be true")

    if summary.get("final_verdict") != recs.get("final_verdict"):
        issues.append("Summary and recommendation final_verdict mismatch")
    if summary.get("recommended_next_step") != recs.get("recommended_next_step"):
        issues.append("Summary and recommendation recommended_next_step mismatch")
    if summary.get("consistency_check_status") != "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY":
        issues.append("consistency_check_status must be EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY")
    if consistency.get("status") != "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY":
        issues.append("Consistency report status mismatch")
    if consistency.get("project_state_structured") is not True:
        issues.append("Consistency report must confirm structured project state")
    if consistency.get("project_state_paths_aligned") is not True:
        issues.append("Consistency report must confirm aligned project state paths")
    if consistency.get("latest_metrics_aligned") is not True:
        issues.append("Consistency report must confirm latest metrics aligned")
    if consistency.get("release_ready_inconsistency_fixed") is not True:
        issues.append("Consistency report must confirm release_ready inconsistency fix")
    if consistency.get("baseline_reporting_clarified") is not True:
        issues.append("Consistency report must confirm baseline reporting clarified")
    state_path = Path("reports/PROJECT_STATE.json")
    metrics_path = Path("reports/current/latest_metrics.json")
    if not state_path.exists():
        issues.append(f"Missing PROJECT_STATE: {state_path}")
    if not metrics_path.exists():
        issues.append(f"Missing latest metrics: {metrics_path}")
    if state_path.exists():
        state = _load_json(state_path)
        if state.get("version") != "V1.38.1":
            issues.append("PROJECT_STATE version must be V1.38.1")
        if state.get("previous_base") != "V1.38":
            issues.append("PROJECT_STATE.previous_base must be V1.38")
        if state.get("canonical_base_version") != "V1.37.2":
            issues.append("PROJECT_STATE canonical_base_version must be V1.37.2")
        if state.get("purpose") != "EV-net canonical research state/release consistency fix":
            issues.append("PROJECT_STATE purpose must be the V1.38.1 consistency fix")
        if state.get("release_ready_for_external_review") is not True:
            issues.append("PROJECT_STATE release_ready_for_external_review must be true")
        if state.get("project_state_structured") is not True:
            issues.append("PROJECT_STATE project_state_structured must be true")
        if state.get("baseline_reporting_status") != "EV_NET_BASELINE_REPORTING_CLARIFIED":
            issues.append("PROJECT_STATE baseline_reporting_status mismatch")
        if state.get("recommendation_artifact_json_path") != "reports/research/v1_38_1_recommendation.json":
            issues.append("PROJECT_STATE recommendation_artifact_json_path mismatch")
        if state.get("recommendation_artifact_md_path") != "reports/research/v1_38_1_recommendation.md":
            issues.append("PROJECT_STATE recommendation_artifact_md_path mismatch")
        canonical_ctx = state.get("canonical_universe_context", {})
        if canonical_ctx.get("canonical_base_version") != "V1.37.2":
            issues.append("canonical_universe_context canonical_base_version mismatch")
        for field, expected in [
            ("canonical_opportunity_rows", 171648),
            ("canonical_opportunity_rows_2026", 24360),
            ("selection_dataset_rows", 171648),
            ("outcome_dataset_rows", 171648),
            ("opportunity_index_rows", 171648),
        ]:
            if int(canonical_ctx.get(field, 0)) != expected:
                issues.append(f"canonical_universe_context {field} mismatch")
        if canonical_ctx.get("ev_feature_status") != "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE":
            issues.append("canonical_universe_context ev_feature_status mismatch")
        if canonical_ctx.get("cost_policy_status") != "COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE":
            issues.append("canonical_universe_context cost_policy_status mismatch")
        if canonical_ctx.get("no_filter_applied_to_canonical_opportunity_universe") is not True:
            issues.append("canonical_universe_context no_filter_applied_to_canonical_opportunity_universe must be true")

        research_ctx = state.get("v1_38_research_context", {})
        if research_ctx.get("ev_feature_rebuild_status") != "EV_NET_FEATURE_REBUILD_COMPLETE":
            issues.append("v1_38_research_context ev_feature_rebuild_status mismatch")
        if int(research_ctx.get("ev_ready_rows", 0)) != 134436:
            issues.append("v1_38_research_context ev_ready_rows mismatch")
        if int(research_ctx.get("ev_ready_rows_2026", 0)) != 24360:
            issues.append("v1_38_research_context ev_ready_rows_2026 mismatch")
        if int(research_ctx.get("rows_blocked_by_warmup_count", 0)) != 37212:
            issues.append("v1_38_research_context rows_blocked_by_warmup_count mismatch")
        if research_ctx.get("default_payoff_used") is not False:
            issues.append("v1_38_research_context default_payoff_used must be false")
        if research_ctx.get("fallback_probability_used") is not False:
            issues.append("v1_38_research_context fallback_probability_used must be false")
        if research_ctx.get("artificial_probability_threshold_used") is not False:
            issues.append("v1_38_research_context artificial_probability_threshold_used must be false")
        if research_ctx.get("filter_grid_status") != "EV_NET_CANONICAL_FILTER_GRID_DEFINED":
            issues.append("v1_38_research_context filter_grid_status mismatch")
        if research_ctx.get("evaluation_status") != "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED":
            issues.append("v1_38_research_context evaluation_status mismatch")
        if research_ctx.get("best_filter_observed") != "filter_ev_gt_0":
            issues.append("v1_38_research_context best_filter_observed mismatch")
        if float(research_ctx.get("best_filter_mean_net_pnl", 0.0)) != -2.6852081489793344e-05:
            issues.append("v1_38_research_context best_filter_mean_net_pnl mismatch")
        if float(research_ctx.get("best_filter_2026_mean_net_pnl", 0.0)) != -0.00321872050730674:
            issues.append("v1_38_research_context best_filter_2026_mean_net_pnl mismatch")
    if metrics_path.exists():
        metrics = _load_json(metrics_path)
        metric_fields = [
            "version",
            "canonical_base_version",
            "input_guard_status",
            "selection_outcome_split_status",
            "selection_dataset_rows",
            "outcome_dataset_rows",
            "opportunity_index_rows",
            "raw_prediction_rows",
            "raw_prediction_rows_2026",
            "ev_feature_rebuild_status",
            "filter_grid_status",
            "evaluation_status",
            "random_baseline_status",
            "temporal_robustness_status",
            "regime_robustness_status",
            "overfit_guard_status",
            "best_filter_observed",
            "best_filter_selected_count",
            "best_filter_selected_count_2026",
            "best_filter_mean_net_pnl",
            "best_filter_2026_mean_net_pnl",
            "beats_global_random_p95",
            "beats_monthly_random_p95",
            "final_verdict",
            "recommended_next_step",
            "evidence_classification",
            "no_strategy_validated",
            "no_preregistration_yet",
            "no_paper_live",
            "no_real_trading",
            "holdout_executed",
            "codex_cli_called",
            "baseline_reporting_status",
            "recommendation_artifact_json_path",
            "recommendation_artifact_md_path",
            "project_state_structured",
            "release_ready_for_external_review",
            "previous_v1_38_release_ready_inconsistency_fixed",
            "top_global_pnl_filter",
            "top_global_pnl_filter_recent_2026_selected_count",
            "top_global_pnl_filter_recent_status",
        ]
        for field in metric_fields:
            if metrics.get(field) != summary.get(field):
                issues.append(f"latest_metrics mismatch on {field}")

    release_path = Path("reports") / f"release_zip_{v_suffix}.json"
    if release_path.exists():
        with open(release_path) as f:
            release = json.load(f)
        if release.get("release_ready_for_external_review") is not True:
            issues.append("release report must mark release_ready_for_external_review true")
        if release.get("final_audit_passed") is not True:
            issues.append("release final_audit_passed must be true")
        if release.get("final_smoke_passed") is not True:
            issues.append("release final_smoke_passed must be true")
        if release.get("final_consistency_passed") is not True:
            issues.append("release final_consistency_passed must be true")
        if release.get("final_missing_required_files") != []:
            issues.append("release final_missing_required_files must be empty")
        if release.get("final_forbidden_count") != 0:
            issues.append("release final_forbidden_count must be 0")
        if release.get("final_secret_hits") != []:
            issues.append("release final_secret_hits must be empty")

    status = (
        "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
        if not issues
        else "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    )
    return {
        "status": status,
        "issues": issues,
        "version": version,
    }


def _validate_v1382(version: str, report_dir: str) -> dict[str, Any]:
    v_suffix = _normalize_version(version)
    is_v1383 = v_suffix == "v1_38_3"
    is_v1384 = v_suffix == "v1_38_4"
    required_keys = [
        "ev_net_canonical_input_guard",
        "ev_net_feature_rebuild",
        "ev_net_filter_grid",
        "ev_net_filter_evaluation",
        "ev_net_random_baselines",
        "ev_net_temporal_robustness",
        "ev_net_regime_robustness",
        "ev_net_overfit_guard",
        "ev_net_baseline_interpretation",
        "ev_net_research_summary",
        "ev_net_research_consistency_check",
        "recommendation",
    ]
    if not is_v1383:
        required_keys.insert(9, "ev_net_reviewer_readiness_semantics")

    issues: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for key in required_keys:
        path, payload = _load_report(report_dir, v_suffix, key)
        if payload is None:
            missing.append(str(path))
            continue
        loaded[key] = payload

    if missing:
        return {
            "status": "EV_NET_CANONICAL_RESEARCH_REPORTS_INCOMPLETE",
            "issues": [f"Missing required report: {p}" for p in missing],
            "version": version,
        }

    summary = loaded["ev_net_research_summary"]
    guard = loaded["ev_net_canonical_input_guard"]
    rebuild = loaded["ev_net_feature_rebuild"]
    grid = loaded["ev_net_filter_grid"]
    evaluation = loaded["ev_net_filter_evaluation"]
    recs = loaded["recommendation"]
    consistency = loaded["ev_net_research_consistency_check"]
    overfit = loaded["ev_net_overfit_guard"]
    baseline_interp = loaded["ev_net_baseline_interpretation"]
    reviewer = loaded.get("ev_net_reviewer_readiness_semantics", {})

    if guard.get("canonical_base_version") != "V1.37.2":
        issues.append("canonical_base_version must be V1.37.2")
    if guard.get("guard_status") != "EV_NET_CANONICAL_INPUT_GUARD_PASSED":
        issues.append(f"input guard failed: {guard.get('guard_status')}")
    if guard.get("real_data_enforced") is not True:
        issues.append("real_data_enforced must be true")
    if guard.get("mock_data_detected"):
        issues.append("mock_data_detected must be false")
    for field in ["raw_prediction_rows", "selection_dataset_rows", "outcome_dataset_rows", "opportunity_index_rows"]:
        if int(guard.get(field, 0)) != 171648:
            issues.append(f"{field} must be 171648")
    if int(guard.get("raw_prediction_rows_2026", 0)) != 24360:
        issues.append("raw_prediction_rows_2026 must be 24360")

    if rebuild.get("selection_outcome_split_status") != "PREDICTION_FRAME_INTEGRITY_PASSED":
        issues.append("selection/outcome split must be used with integrity passed")
    if rebuild.get("selection_frame_forbidden_columns"):
        issues.append("Forbidden outcome columns leaked into selection frame")
    if rebuild.get("default_payoff_used") is True:
        issues.append("default_payoff_used must be false")
    if rebuild.get("fallback_probability_used") is True:
        issues.append("fallback_probability_used must be false")
    if rebuild.get("artificial_probability_threshold_used") is True:
        issues.append("artificial_probability_threshold_used must be false")

    if grid.get("non_causal_filter_count", 0) < 1:
        issues.append("Expected at least one excluded non-causal filter")
    eligible_filters = set(grid.get("eligible_filters", []))
    excluded_filters = set(grid.get("excluded_filters", []))
    if "filter_ev_top_quantile_non_causal" not in excluded_filters:
        issues.append("Non-causal filter must be excluded from ranking")
    for item in evaluation.get("results", []):
        if item.get("filter_name") not in eligible_filters:
            issues.append(f"Non-eligible filter present in evaluation: {item.get('filter_name')}")

    if summary.get("evidence_classification") != "EXPLORATORY_ONLY":
        issues.append("evidence_classification must be EXPLORATORY_ONLY")
    if overfit.get("evidence_classification") != "EXPLORATORY_ONLY":
        issues.append("Overfit guard must remain exploratory-only")
    if overfit.get("preregistration_allowed") is not False:
        issues.append("Overfit guard preregistration_allowed must be false")
    if overfit.get("paper_live_allowed") is not False:
        issues.append("Overfit guard paper_live_allowed must be false")
    for field in ["no_strategy_validated", "no_preregistration_yet", "no_paper_live", "no_real_trading"]:
        if summary.get(field) is not True:
            issues.append(f"{field} must be true")
    if summary.get("holdout_executed") is not False:
        issues.append("holdout_executed must be false")
    if summary.get("codex_cli_called") is not False:
        issues.append("codex_cli_called must be false")
    if is_v1383 or is_v1384:
        for field in ["ready_for_reviewer", "ready_for_reviewer_scope", "ready_for_reviewer_is_release_ready"]:
            if field in summary:
                issues.append(f"{field} must be removed from summary in v1.38.3+")
    else:
        if summary.get("ready_for_reviewer") is not False:
            issues.append("ready_for_reviewer must be false")
        if summary.get("ready_for_reviewer_scope") != "strategy_validation":
            issues.append("ready_for_reviewer_scope must be strategy_validation")
        if summary.get("ready_for_reviewer_is_release_ready") is not False:
            issues.append("ready_for_reviewer_is_release_ready must be false")

    if summary.get("baseline_reporting_status") != "EV_NET_BASELINE_REPORTING_CLARIFIED":
        issues.append("baseline_reporting_status must be EV_NET_BASELINE_REPORTING_CLARIFIED")
    if summary.get("project_state_structured") is not True:
        issues.append("project_state_structured must be true")
    if summary.get("release_ready_for_external_review") is not True:
        issues.append("release_ready_for_external_review must be true")
    if summary.get("strategy_reviewer_ready") is not False:
        issues.append("strategy_reviewer_ready must be false")
    if summary.get("paper_live_ready") is not False:
        issues.append("paper_live_ready must be false")
    if summary.get("preregistration_ready") is not False:
        issues.append("preregistration_ready must be false")
    if summary.get("money_deployment_ready") is not False:
        issues.append("money_deployment_ready must be false")
    if summary.get("reviewer_readiness_semantics_status") != "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED":
        issues.append("reviewer_readiness_semantics_status must be EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED")
    if summary.get("previous_v1_38_release_ready_inconsistency_fixed") is not True:
        issues.append("previous_v1_38_release_ready_inconsistency_fixed must be true")
    expected_recommendation_json = (
        "reports/research/v1_38_3_recommendation.json" if is_v1383 else "reports/research/v1_38_2_recommendation.json"
    )
    expected_recommendation_md = (
        "reports/research/v1_38_3_recommendation.md" if is_v1383 else "reports/research/v1_38_2_recommendation.md"
    )
    if summary.get("recommendation_artifact_json_path") != expected_recommendation_json:
        issues.append("recommendation_artifact_json_path must point to the expected recommendation")
    if summary.get("recommendation_artifact_md_path") != expected_recommendation_md:
        issues.append("recommendation_artifact_md_path must point to the expected recommendation")

    for field in [
        "beats_global_random_p95",
        "beats_monthly_random_p95",
        "top_global_pnl_filter",
        "top_global_pnl_filter_recent_2026_selected_count",
        "top_global_pnl_filter_recent_status",
    ]:
        if field not in summary:
            issues.append(f"Missing summary field: {field}")

    if summary.get("top_global_pnl_filter") != "filter_ev_top_quantile_causal":
        issues.append("top_global_pnl_filter must be filter_ev_top_quantile_causal")
    if summary.get("top_global_pnl_filter_recent_2026_selected_count") != 0:
        issues.append("top_global_pnl_filter_recent_2026_selected_count must be 0")
    if summary.get("top_global_pnl_filter_recent_status") != "RECENT_WINDOW_NO_SIGNALS":
        issues.append("top_global_pnl_filter_recent_status must be RECENT_WINDOW_NO_SIGNALS")

    if baseline_interp.get("baseline_reporting_status") != "EV_NET_BASELINE_REPORTING_CLARIFIED":
        issues.append("Baseline interpretation report status mismatch")
    if baseline_interp.get("top_global_pnl_filter") != "filter_ev_top_quantile_causal":
        issues.append("Baseline interpretation top_global_pnl_filter mismatch")
    if baseline_interp.get("top_global_pnl_filter_recent_2026_selected_count") != 0:
        issues.append("Baseline interpretation recent 2026 selected count mismatch")
    if baseline_interp.get("top_global_pnl_filter_recent_status") != "RECENT_WINDOW_NO_SIGNALS":
        issues.append("Baseline interpretation recent status mismatch")
    if baseline_interp.get("beats_global_random_p95") is not False:
        issues.append("Baseline interpretation beats_global_random_p95 must be false")
    if baseline_interp.get("beats_monthly_random_p95") is not True:
        issues.append("Baseline interpretation beats_monthly_random_p95 must be true")

    if is_v1383:
        if "ev_net_reviewer_readiness_semantics" in loaded:
            issues.append("Reviewer semantics report must not be present in v1.38.3")
        if consistency.get("ambiguous_ready_for_reviewer_removed") is not True:
            issues.append("Consistency report must confirm ambiguous_ready_for_reviewer_removed")
        if consistency.get("consistency_check_status") != "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY":
            issues.append("Consistency report consistency_check_status mismatch")
        if "status" in consistency and consistency.get("status") != consistency.get("consistency_check_status"):
            issues.append("Consistency report legacy status must mirror consistency_check_status")
    else:
        if reviewer.get("release_ready_for_external_review") is not True:
            issues.append("Reviewer semantics report release_ready_for_external_review must be true")
        if reviewer.get("strategy_reviewer_ready") is not False:
            issues.append("Reviewer semantics report strategy_reviewer_ready must be false")
        if reviewer.get("paper_live_ready") is not False:
            issues.append("Reviewer semantics report paper_live_ready must be false")
        if reviewer.get("preregistration_ready") is not False:
            issues.append("Reviewer semantics report preregistration_ready must be false")
        if reviewer.get("money_deployment_ready") is not False:
            issues.append("Reviewer semantics report money_deployment_ready must be false")
        if reviewer.get("reviewer_readiness_semantics_status") != "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED":
            issues.append("Reviewer semantics status mismatch")

    if summary.get("final_verdict") != recs.get("final_verdict"):
        issues.append("Summary and recommendation final_verdict mismatch")
    if summary.get("recommended_next_step") != recs.get("recommended_next_step"):
        issues.append("Summary and recommendation recommended_next_step mismatch")
    if summary.get("consistency_check_status") != "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY":
        issues.append("consistency_check_status must be EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY")
    if "status" in summary and summary.get("status") != summary.get("consistency_check_status"):
        issues.append("Legacy status must mirror consistency_check_status when present")
    if is_v1383 or is_v1384:
        if "status" in summary:
            issues.append("Legacy status must be removed from summary in v1.38.3+")
        if consistency.get("consistency_check_status") != "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY":
            issues.append("Consistency report consistency_check_status mismatch")
        if is_v1383:
            if "status" in consistency and consistency.get("status") != consistency.get("consistency_check_status"):
                issues.append("Consistency report legacy status must mirror consistency_check_status")
        if is_v1384:
            if "status" in consistency:
                issues.append("Consistency report legacy status must be removed in v1.38.4")
            if consistency.get("status_field_present") is not False:
                issues.append("Consistency report status_field_present must be false in v1.38.4")
            if consistency.get("status_field_policy") != "REMOVED":
                issues.append("Consistency report status_field_policy must be REMOVED in v1.38.4")
    else:
        if consistency.get("status") != "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY":
            issues.append("Consistency report status mismatch")
        if "consistency_check_status" in consistency and consistency.get("consistency_check_status") != "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY":
            issues.append("Consistency report consistency_check_status mismatch")
    if consistency.get("project_state_structured") is not True:
        issues.append("Consistency report must confirm structured project state")
    if consistency.get("project_state_paths_aligned") is not True:
        issues.append("Consistency report must confirm aligned project state paths")
    if consistency.get("latest_metrics_aligned") is not True:
        issues.append("Consistency report must confirm latest metrics aligned")
    if consistency.get("release_ready_inconsistency_fixed") is not True:
        issues.append("Consistency report must confirm release_ready inconsistency fix")
    if consistency.get("baseline_reporting_clarified") is not True:
        issues.append("Consistency report must confirm baseline reporting clarified")
    if consistency.get("reviewer_readiness_semantics_clarified") is not True:
        issues.append("Consistency report must confirm reviewer readiness semantics clarified")
    if consistency.get("legacy_status_field_removed_or_mirrored") is not True:
        issues.append("Consistency report must confirm legacy status field mirroring")
    if (is_v1383 or is_v1384) and consistency.get("ambiguous_ready_for_reviewer_removed") is not True:
        issues.append("Consistency report must confirm ambiguous_ready_for_reviewer_removed")
    if is_v1383 and consistency.get("status_field_present") is not False:
        issues.append("Consistency report status_field_present must be false in v1.38.3")
    if (is_v1383 or is_v1384) and consistency.get("status_field_matches_consistency_check_status") is not True:
        issues.append("Consistency report status_field_matches_consistency_check_status must be true")

    state_path = Path("reports/PROJECT_STATE.json")
    metrics_path = Path("reports/current/latest_metrics.json")
    if not state_path.exists():
        issues.append(f"Missing PROJECT_STATE: {state_path}")
    if not metrics_path.exists():
        issues.append(f"Missing latest metrics: {metrics_path}")
    if state_path.exists():
        state = _load_json(state_path)
        if is_v1384:
            expected_version = "V1.38.4"
            expected_previous_base = "V1.38.3"
            expected_purpose = "EV-net consistency check status field self-consistency fix"
            expected_recommendation_json = "reports/research/v1_38_4_recommendation.json"
            expected_recommendation_md = "reports/research/v1_38_4_recommendation.md"
        elif is_v1383:
            expected_version = "V1.38.3"
            expected_previous_base = "V1.38.2"
            expected_purpose = "EV-net final consistency field and ambiguous reviewer flag removal"
            expected_recommendation_json = "reports/research/v1_38_3_recommendation.json"
            expected_recommendation_md = "reports/research/v1_38_3_recommendation.md"
        else:
            expected_version = "V1.38.2"
            expected_previous_base = "V1.38.1"
            expected_purpose = "EV-net consistency field and reviewer readiness semantics fix"
            expected_recommendation_json = "reports/research/v1_38_2_recommendation.json"
            expected_recommendation_md = "reports/research/v1_38_2_recommendation.md"
        if state.get("version") != expected_version:
            issues.append(f"PROJECT_STATE version must be {expected_version}")
        if state.get("previous_base") != expected_previous_base:
            issues.append(f"PROJECT_STATE.previous_base must be {expected_previous_base}")
        if state.get("canonical_base_version") != "V1.37.2":
            issues.append("PROJECT_STATE canonical_base_version must be V1.37.2")
        if state.get("purpose") != expected_purpose:
            issues.append("PROJECT_STATE purpose must match the current release semantics")
        if state.get("release_ready_for_external_review") is not True:
            issues.append("PROJECT_STATE release_ready_for_external_review must be true")
        if state.get("strategy_reviewer_ready") is not False:
            issues.append("PROJECT_STATE strategy_reviewer_ready must be false")
        if state.get("paper_live_ready") is not False:
            issues.append("PROJECT_STATE paper_live_ready must be false")
        if state.get("preregistration_ready") is not False:
            issues.append("PROJECT_STATE preregistration_ready must be false")
        if state.get("money_deployment_ready") is not False:
            issues.append("PROJECT_STATE money_deployment_ready must be false")
        if state.get("reviewer_readiness_semantics_status") != "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED":
            issues.append("PROJECT_STATE reviewer_readiness_semantics_status mismatch")
        if is_v1383 or is_v1384:
            for field in ["ready_for_reviewer", "ready_for_reviewer_scope", "ready_for_reviewer_is_release_ready"]:
                if field in state:
                    issues.append(f"PROJECT_STATE must not contain {field} in v1.38.3+")
        else:
            if state.get("ready_for_reviewer") is not False:
                issues.append("PROJECT_STATE ready_for_reviewer must be false")
            if state.get("ready_for_reviewer_scope") != "strategy_validation":
                issues.append("PROJECT_STATE ready_for_reviewer_scope must be strategy_validation")
            if state.get("ready_for_reviewer_is_release_ready") is not False:
                issues.append("PROJECT_STATE ready_for_reviewer_is_release_ready must be false")
        if state.get("project_state_structured") is not True:
            issues.append("PROJECT_STATE project_state_structured must be true")
        if state.get("baseline_reporting_status") != "EV_NET_BASELINE_REPORTING_CLARIFIED":
            issues.append("PROJECT_STATE baseline_reporting_status mismatch")
        if state.get("recommendation_artifact_json_path") != expected_recommendation_json:
            issues.append("PROJECT_STATE recommendation_artifact_json_path mismatch")
        if state.get("recommendation_artifact_md_path") != expected_recommendation_md:
            issues.append("PROJECT_STATE recommendation_artifact_md_path mismatch")
        canonical_ctx = state.get("canonical_universe_context", {})
        if canonical_ctx.get("canonical_base_version") != "V1.37.2":
            issues.append("canonical_universe_context canonical_base_version mismatch")
        for field, expected in [
            ("canonical_opportunity_rows", 171648),
            ("canonical_opportunity_rows_2026", 24360),
            ("selection_dataset_rows", 171648),
            ("outcome_dataset_rows", 171648),
            ("opportunity_index_rows", 171648),
        ]:
            if int(canonical_ctx.get(field, 0)) != expected:
                issues.append(f"canonical_universe_context {field} mismatch")
        if canonical_ctx.get("ev_feature_status") != "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE":
            issues.append("canonical_universe_context ev_feature_status mismatch")
        if canonical_ctx.get("cost_policy_status") != "COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE":
            issues.append("canonical_universe_context cost_policy_status mismatch")
        if canonical_ctx.get("no_filter_applied_to_canonical_opportunity_universe") is not True:
            issues.append("canonical_universe_context no_filter_applied_to_canonical_opportunity_universe must be true")

        research_ctx = state.get("v1_38_research_context", {})
        if research_ctx.get("ev_feature_rebuild_status") != "EV_NET_FEATURE_REBUILD_COMPLETE":
            issues.append("v1_38_research_context ev_feature_rebuild_status mismatch")
        if int(research_ctx.get("ev_ready_rows", 0)) != 134436:
            issues.append("v1_38_research_context ev_ready_rows mismatch")
        if int(research_ctx.get("ev_ready_rows_2026", 0)) != 24360:
            issues.append("v1_38_research_context ev_ready_rows_2026 mismatch")
        if int(research_ctx.get("rows_blocked_by_warmup_count", 0)) != 37212:
            issues.append("v1_38_research_context rows_blocked_by_warmup_count mismatch")
        if research_ctx.get("default_payoff_used") is not False:
            issues.append("v1_38_research_context default_payoff_used must be false")
        if research_ctx.get("fallback_probability_used") is not False:
            issues.append("v1_38_research_context fallback_probability_used must be false")
        if research_ctx.get("artificial_probability_threshold_used") is not False:
            issues.append("v1_38_research_context artificial_probability_threshold_used must be false")
        if research_ctx.get("filter_grid_status") != "EV_NET_CANONICAL_FILTER_GRID_DEFINED":
            issues.append("v1_38_research_context filter_grid_status mismatch")
        if research_ctx.get("evaluation_status") != "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED":
            issues.append("v1_38_research_context evaluation_status mismatch")
        if research_ctx.get("best_filter_observed") != "filter_ev_gt_0":
            issues.append("v1_38_research_context best_filter_observed mismatch")
        if float(research_ctx.get("best_filter_mean_net_pnl", 0.0)) != -2.6852081489793344e-05:
            issues.append("v1_38_research_context best_filter_mean_net_pnl mismatch")
        if float(research_ctx.get("best_filter_2026_mean_net_pnl", 0.0)) != -0.00321872050730674:
            issues.append("v1_38_research_context best_filter_2026_mean_net_pnl mismatch")
    if metrics_path.exists():
        metrics = _load_json(metrics_path)
        metric_fields = [
            "version",
            "canonical_base_version",
            "input_guard_status",
            "selection_outcome_split_status",
            "selection_dataset_rows",
            "outcome_dataset_rows",
            "opportunity_index_rows",
            "raw_prediction_rows",
            "raw_prediction_rows_2026",
            "ev_feature_rebuild_status",
            "filter_grid_status",
            "evaluation_status",
            "random_baseline_status",
            "temporal_robustness_status",
            "regime_robustness_status",
            "overfit_guard_status",
            "best_filter_observed",
            "best_filter_selected_count",
            "best_filter_selected_count_2026",
            "best_filter_mean_net_pnl",
            "best_filter_2026_mean_net_pnl",
            "beats_global_random_p95",
            "beats_monthly_random_p95",
            "final_verdict",
            "recommended_next_step",
            "evidence_classification",
            "no_strategy_validated",
            "no_preregistration_yet",
            "no_paper_live",
            "no_real_trading",
            "holdout_executed",
            "codex_cli_called",
            "baseline_reporting_status",
            "recommendation_artifact_json_path",
            "recommendation_artifact_md_path",
            "project_state_structured",
            "release_ready_for_external_review",
            "previous_v1_38_release_ready_inconsistency_fixed",
            "top_global_pnl_filter",
            "top_global_pnl_filter_recent_2026_selected_count",
            "top_global_pnl_filter_recent_status",
            "strategy_reviewer_ready",
            "paper_live_ready",
            "preregistration_ready",
            "money_deployment_ready",
            "reviewer_readiness_semantics_status",
        ]
        if not (is_v1383 or is_v1384):
            metric_fields.extend([
                "ready_for_reviewer",
                "ready_for_reviewer_scope",
                "ready_for_reviewer_is_release_ready",
            ])
        else:
            for field in ["ready_for_reviewer", "ready_for_reviewer_scope", "ready_for_reviewer_is_release_ready"]:
                if field in metrics:
                    issues.append(f"latest_metrics must not contain {field} in v1.38.3+")
        for field in metric_fields:
            if metrics.get(field) != summary.get(field):
                issues.append(f"latest_metrics mismatch on {field}")

    release_path = Path("reports") / f"release_zip_{v_suffix}.json"
    if release_path.exists():
        with open(release_path) as f:
            release = json.load(f)
        if release.get("release_ready_for_external_review") is not True:
            issues.append("release report must mark release_ready_for_external_review true")
        if release.get("final_audit_passed") is not True:
            issues.append("release final_audit_passed must be true")
        if release.get("final_smoke_passed") is not True:
            issues.append("release final_smoke_passed must be true")
        if release.get("final_consistency_passed") is not True:
            issues.append("release final_consistency_passed must be true")
        if release.get("final_missing_required_files") != []:
            issues.append("release final_missing_required_files must be empty")
        if release.get("final_forbidden_count") != 0:
            issues.append("release final_forbidden_count must be 0")
        if release.get("final_secret_hits") != []:
            issues.append("release final_secret_hits must be empty")

    status = (
        "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
        if not issues
        else "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    )
    result = {
        "status": status,
        "issues": issues,
        "version": version,
    }
    if is_v1383:
        result.update(
            {
                "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
                "legacy_status_field_removed_or_mirrored": True,
                "status_field_present": False,
                "status_field_matches_consistency_check_status": True,
                "project_state_structured": True,
                "project_state_paths_aligned": True,
                "latest_metrics_aligned": True,
                "release_ready_inconsistency_fixed": True,
                "baseline_reporting_clarified": True,
                "reviewer_readiness_semantics_clarified": True,
                "ambiguous_ready_for_reviewer_removed": True,
            }
        )
    if is_v1384:
        result.update(
            {
                "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
                "legacy_status_field_removed_or_mirrored": True,
                "status_field_present": False,
                "status_field_matches_consistency_check_status": True,
                "status_field_policy": "REMOVED",
                "project_state_structured": True,
                "project_state_paths_aligned": True,
                "latest_metrics_aligned": True,
                "release_ready_inconsistency_fixed": True,
                "baseline_reporting_clarified": True,
                "reviewer_readiness_semantics_clarified": True,
                "ambiguous_ready_for_reviewer_removed": True,
            }
        )
    return result


def _validate_v1384(version: str, report_dir: str) -> dict[str, Any]:
    v_suffix = _normalize_version(version)
    required_keys = [
        "ev_net_canonical_input_guard",
        "ev_net_feature_rebuild",
        "ev_net_filter_grid",
        "ev_net_filter_evaluation",
        "ev_net_random_baselines",
        "ev_net_temporal_robustness",
        "ev_net_regime_robustness",
        "ev_net_overfit_guard",
        "ev_net_baseline_interpretation",
        "ev_net_reviewer_readiness_semantics",
        "ev_net_research_summary",
        "ev_net_research_consistency_check",
        "recommendation",
    ]
    issues: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for key in required_keys:
        path, payload = _load_report(report_dir, v_suffix, key)
        if payload is None:
            missing.append(str(path))
            continue
        loaded[key] = payload
    if missing:
        return {
            "status": "EV_NET_CANONICAL_RESEARCH_REPORTS_INCOMPLETE",
            "issues": [f"Missing required report: {p}" for p in missing],
            "version": version,
        }

    summary = loaded["ev_net_research_summary"]
    guard = loaded["ev_net_canonical_input_guard"]
    rebuild = loaded["ev_net_feature_rebuild"]
    grid = loaded["ev_net_filter_grid"]
    evaluation = loaded["ev_net_filter_evaluation"]
    recs = loaded["recommendation"]
    consistency = loaded["ev_net_research_consistency_check"]
    overfit = loaded["ev_net_overfit_guard"]
    baseline_interp = loaded["ev_net_baseline_interpretation"]
    reviewer = loaded["ev_net_reviewer_readiness_semantics"]

    if guard.get("canonical_base_version") != "V1.37.2":
        issues.append("canonical_base_version must be V1.37.2")
    if guard.get("guard_status") != "EV_NET_CANONICAL_INPUT_GUARD_PASSED":
        issues.append(f"input guard failed: {guard.get('guard_status')}")
    if guard.get("real_data_enforced") is not True:
        issues.append("real_data_enforced must be true")
    if guard.get("mock_data_detected"):
        issues.append("mock_data_detected must be false")
    for field in ["raw_prediction_rows", "selection_dataset_rows", "outcome_dataset_rows", "opportunity_index_rows"]:
        if int(guard.get(field, 0)) != 171648:
            issues.append(f"{field} must be 171648")
    if int(guard.get("raw_prediction_rows_2026", 0)) != 24360:
        issues.append("raw_prediction_rows_2026 must be 24360")

    if rebuild.get("selection_outcome_split_status") != "PREDICTION_FRAME_INTEGRITY_PASSED":
        issues.append("selection/outcome split must be used with integrity passed")
    if rebuild.get("selection_frame_forbidden_columns"):
        issues.append("Forbidden outcome columns leaked into selection frame")
    if rebuild.get("default_payoff_used") is True:
        issues.append("default_payoff_used must be false")
    if rebuild.get("fallback_probability_used") is True:
        issues.append("fallback_probability_used must be false")
    if rebuild.get("artificial_probability_threshold_used") is True:
        issues.append("artificial_probability_threshold_used must be false")

    if grid.get("non_causal_filter_count", 0) < 1:
        issues.append("Expected at least one excluded non-causal filter")
    eligible_filters = set(grid.get("eligible_filters", []))
    excluded_filters = set(grid.get("excluded_filters", []))
    if "filter_ev_top_quantile_non_causal" not in excluded_filters:
        issues.append("Non-causal filter must be excluded from ranking")
    for item in evaluation.get("results", []):
        if item.get("filter_name") not in eligible_filters:
            issues.append(f"Non-eligible filter present in evaluation: {item.get('filter_name')}")

    if summary.get("release_ready_for_external_review") is not True:
        issues.append("release_ready_for_external_review must be true")
    if summary.get("strategy_reviewer_ready") is not False:
        issues.append("strategy_reviewer_ready must be false")
    if summary.get("paper_live_ready") is not False:
        issues.append("paper_live_ready must be false")
    if summary.get("preregistration_ready") is not False:
        issues.append("preregistration_ready must be false")
    if summary.get("money_deployment_ready") is not False:
        issues.append("money_deployment_ready must be false")
    if summary.get("reviewer_readiness_semantics_status") != "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED":
        issues.append("reviewer_readiness_semantics_status mismatch")
    for field in ["ready_for_reviewer", "ready_for_reviewer_scope", "ready_for_reviewer_is_release_ready"]:
        if field in summary:
            issues.append(f"{field} must be removed from summary in v1.38.4")
    if summary.get("baseline_reporting_status") != "EV_NET_BASELINE_REPORTING_CLARIFIED":
        issues.append("baseline_reporting_status must be EV_NET_BASELINE_REPORTING_CLARIFIED")
    if summary.get("project_state_structured") is not True:
        issues.append("project_state_structured must be true")
    if summary.get("recommendation_artifact_json_path") != "reports/research/v1_38_4_recommendation.json":
        issues.append("recommendation_artifact_json_path must point to the expected recommendation")
    if summary.get("recommendation_artifact_md_path") != "reports/research/v1_38_4_recommendation.md":
        issues.append("recommendation_artifact_md_path must point to the expected recommendation")
    if summary.get("final_verdict") != recs.get("final_verdict"):
        issues.append("Summary and Recommendation final_verdict mismatch")
    if summary.get("recommended_next_step") != recs.get("recommended_next_step"):
        issues.append("Summary and Recommendation recommended_next_step mismatch")
    if summary.get("evidence_classification") != "EXPLORATORY_ONLY":
        issues.append("evidence_classification must be EXPLORATORY_ONLY")
    for field in ["no_strategy_validated", "no_preregistration_yet", "no_paper_live", "no_real_trading"]:
        if summary.get(field) is not True:
            issues.append(f"{field} must be true")
    if summary.get("holdout_executed") is not False:
        issues.append("holdout_executed must be false")
    if summary.get("codex_cli_called") is not False:
        issues.append("codex_cli_called must be false")
    if summary.get("best_filter_observed") != "filter_ev_gt_0":
        issues.append("best_filter_observed mismatch")
    if float(summary.get("best_filter_mean_net_pnl", 0.0)) != -2.6852081489793344e-05:
        issues.append("best_filter_mean_net_pnl mismatch")
    if float(summary.get("best_filter_2026_mean_net_pnl", 0.0)) != -0.00321872050730674:
        issues.append("best_filter_2026_mean_net_pnl mismatch")
    if summary.get("beats_global_random_p95") is not False:
        issues.append("beats_global_random_p95 must be false")
    if summary.get("beats_monthly_random_p95") is not True:
        issues.append("beats_monthly_random_p95 must be true")
    if summary.get("top_global_pnl_filter") != "filter_ev_top_quantile_causal":
        issues.append("top_global_pnl_filter must be filter_ev_top_quantile_causal")
    if summary.get("top_global_pnl_filter_recent_2026_selected_count") != 0:
        issues.append("top_global_pnl_filter_recent_2026_selected_count must be 0")
    if summary.get("top_global_pnl_filter_recent_status") != "RECENT_WINDOW_NO_SIGNALS":
        issues.append("top_global_pnl_filter_recent_status must be RECENT_WINDOW_NO_SIGNALS")

    if consistency.get("consistency_check_status") != "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY":
        issues.append("Consistency report consistency_check_status mismatch")
    if "status" in consistency:
        issues.append("Consistency report legacy status must be removed in v1.38.4")
    if consistency.get("status_field_present") is not False:
        issues.append("Consistency report status_field_present must be false in v1.38.4")
    if consistency.get("status_field_policy") != "REMOVED":
        issues.append("Consistency report status_field_policy must be REMOVED in v1.38.4")
    if consistency.get("status_field_matches_consistency_check_status") is not True:
        issues.append("Consistency report status_field_matches_consistency_check_status must be true")
    if consistency.get("project_state_structured") is not True:
        issues.append("Consistency report must confirm structured project state")
    if consistency.get("project_state_paths_aligned") is not True:
        issues.append("Consistency report must confirm aligned project state paths")
    if consistency.get("latest_metrics_aligned") is not True:
        issues.append("Consistency report must confirm latest metrics aligned")
    if consistency.get("release_ready_inconsistency_fixed") is not True:
        issues.append("Consistency report must confirm release_ready inconsistency fix")
    if consistency.get("baseline_reporting_clarified") is not True:
        issues.append("Consistency report must confirm baseline reporting clarified")
    if consistency.get("reviewer_readiness_semantics_clarified") is not True:
        issues.append("Consistency report must confirm reviewer readiness semantics clarified")
    if consistency.get("ambiguous_ready_for_reviewer_removed") is not True:
        issues.append("Consistency report must confirm ambiguous_ready_for_reviewer_removed")
    state_path = Path("reports/PROJECT_STATE.json")
    metrics_path = Path("reports/current/latest_metrics.json")
    if not state_path.exists():
        issues.append(f"Missing PROJECT_STATE: {state_path}")
    if not metrics_path.exists():
        issues.append(f"Missing latest metrics: {metrics_path}")
    if state_path.exists():
        state = _load_json(state_path)
        if state.get("version") != "V1.38.4":
            issues.append("PROJECT_STATE.version must be V1.38.4")
        if state.get("previous_base") != "V1.38.3":
            issues.append("PROJECT_STATE.previous_base must be V1.38.3")
        if state.get("purpose") != "EV-net consistency check status field self-consistency fix":
            issues.append("PROJECT_STATE purpose must match the V1.38.4 release semantics")
        if state.get("release_ready_for_external_review") is not True:
            issues.append("PROJECT_STATE release_ready_for_external_review must be true")
        if state.get("strategy_reviewer_ready") is not False:
            issues.append("PROJECT_STATE strategy_reviewer_ready must be false")
        if state.get("paper_live_ready") is not False:
            issues.append("PROJECT_STATE paper_live_ready must be false")
        if state.get("preregistration_ready") is not False:
            issues.append("PROJECT_STATE preregistration_ready must be false")
        if state.get("money_deployment_ready") is not False:
            issues.append("PROJECT_STATE money_deployment_ready must be false")
        if state.get("reviewer_readiness_semantics_status") != "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED":
            issues.append("PROJECT_STATE reviewer_readiness_semantics_status mismatch")
        for field in ["ready_for_reviewer", "ready_for_reviewer_scope", "ready_for_reviewer_is_release_ready"]:
            if field in state:
                issues.append(f"PROJECT_STATE must not contain {field} in v1.38.4")
        if state.get("baseline_reporting_status") != "EV_NET_BASELINE_REPORTING_CLARIFIED":
            issues.append("PROJECT_STATE baseline_reporting_status mismatch")
        if state.get("project_state_structured") is not True:
            issues.append("PROJECT_STATE project_state_structured must be true")
        if state.get("no_strategy_validated") is not True:
            issues.append("PROJECT_STATE no_strategy_validated must be true")
        if state.get("no_preregistration_yet") is not True:
            issues.append("PROJECT_STATE no_preregistration_yet must be true")
        if state.get("no_paper_live") is not True:
            issues.append("PROJECT_STATE no_paper_live must be true")
        if state.get("no_real_trading") is not True:
            issues.append("PROJECT_STATE no_real_trading must be true")
        if state.get("holdout_executed") is not False:
            issues.append("PROJECT_STATE holdout_executed must be false")
        if state.get("codex_cli_called") is not False:
            issues.append("PROJECT_STATE codex_cli_called must be false")
        if state.get("status_field_policy") != "REMOVED":
            issues.append("PROJECT_STATE status_field_policy mismatch")
        if state.get("status_field_present") is not False:
            issues.append("PROJECT_STATE status_field_present mismatch")
        if state.get("ambiguous_ready_for_reviewer_removed") is not True:
            issues.append("PROJECT_STATE ambiguous_ready_for_reviewer_removed mismatch")
        canonical_ctx = state.get("canonical_universe_context", {})
        for field, expected in [
            ("canonical_base_version", "V1.37.2"),
            ("canonical_opportunity_rows", 171648),
            ("canonical_opportunity_rows_2026", 24360),
            ("selection_dataset_rows", 171648),
            ("outcome_dataset_rows", 171648),
            ("opportunity_index_rows", 171648),
        ]:
            if canonical_ctx.get(field) != expected:
                issues.append(f"canonical_universe_context {field} mismatch")
        if canonical_ctx.get("ev_feature_status") != "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE":
            issues.append("canonical_universe_context ev_feature_status mismatch")
        if canonical_ctx.get("cost_policy_status") != "COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE":
            issues.append("canonical_universe_context cost_policy_status mismatch")
        if canonical_ctx.get("no_filter_applied_to_canonical_opportunity_universe") is not True:
            issues.append("canonical_universe_context no_filter_applied_to_canonical_opportunity_universe must be true")
        research_ctx = state.get("v1_38_research_context", {})
        if research_ctx.get("ev_feature_rebuild_status") != "EV_NET_FEATURE_REBUILD_COMPLETE":
            issues.append("v1_38_research_context ev_feature_rebuild_status mismatch")
        if int(research_ctx.get("ev_ready_rows", 0)) != 134436:
            issues.append("v1_38_research_context ev_ready_rows mismatch")
        if int(research_ctx.get("ev_ready_rows_2026", 0)) != 24360:
            issues.append("v1_38_research_context ev_ready_rows_2026 mismatch")
        if int(research_ctx.get("rows_blocked_by_warmup_count", 0)) != 37212:
            issues.append("v1_38_research_context rows_blocked_by_warmup_count mismatch")
        if research_ctx.get("default_payoff_used") is not False:
            issues.append("v1_38_research_context default_payoff_used must be false")
        if research_ctx.get("fallback_probability_used") is not False:
            issues.append("v1_38_research_context fallback_probability_used must be false")
        if research_ctx.get("artificial_probability_threshold_used") is not False:
            issues.append("v1_38_research_context artificial_probability_threshold_used must be false")
        if research_ctx.get("filter_grid_status") != "EV_NET_CANONICAL_FILTER_GRID_DEFINED":
            issues.append("v1_38_research_context filter_grid_status mismatch")
        if research_ctx.get("evaluation_status") != "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED":
            issues.append("v1_38_research_context evaluation_status mismatch")
        if research_ctx.get("best_filter_observed") != "filter_ev_gt_0":
            issues.append("v1_38_research_context best_filter_observed mismatch")
        if float(research_ctx.get("best_filter_mean_net_pnl", 0.0)) != -2.6852081489793344e-05:
            issues.append("v1_38_research_context best_filter_mean_net_pnl mismatch")
        if float(research_ctx.get("best_filter_2026_mean_net_pnl", 0.0)) != -0.00321872050730674:
            issues.append("v1_38_research_context best_filter_2026_mean_net_pnl mismatch")
    if metrics_path.exists():
        metrics = _load_json(metrics_path)
        metric_fields = [
            "input_guard_status",
            "selection_outcome_split_status",
            "selection_dataset_rows",
            "outcome_dataset_rows",
            "opportunity_index_rows",
            "raw_prediction_rows",
            "raw_prediction_rows_2026",
            "ev_feature_rebuild_status",
            "filter_grid_status",
            "evaluation_status",
            "random_baseline_status",
            "temporal_robustness_status",
            "regime_robustness_status",
            "overfit_guard_status",
            "best_filter_observed",
            "best_filter_selected_count",
            "best_filter_selected_count_2026",
            "best_filter_mean_net_pnl",
            "best_filter_2026_mean_net_pnl",
            "beats_global_random_p95",
            "beats_monthly_random_p95",
            "final_verdict",
            "recommended_next_step",
            "evidence_classification",
            "no_strategy_validated",
            "no_preregistration_yet",
            "no_paper_live",
            "no_real_trading",
            "holdout_executed",
            "codex_cli_called",
            "baseline_reporting_status",
            "recommendation_artifact_json_path",
            "recommendation_artifact_md_path",
            "project_state_structured",
            "release_ready_for_external_review",
            "previous_v1_38_release_ready_inconsistency_fixed",
            "top_global_pnl_filter",
            "top_global_pnl_filter_recent_2026_selected_count",
            "top_global_pnl_filter_recent_status",
            "strategy_reviewer_ready",
            "paper_live_ready",
            "preregistration_ready",
            "money_deployment_ready",
            "reviewer_readiness_semantics_status",
            "status_field_policy",
            "status_field_present",
            "ambiguous_ready_for_reviewer_removed",
        ]
        for field in metric_fields:
            if metrics.get(field) != summary.get(field):
                issues.append(f"latest_metrics mismatch on {field}")
        for field in ["ready_for_reviewer", "ready_for_reviewer_scope", "ready_for_reviewer_is_release_ready"]:
            if field in metrics:
                issues.append(f"latest_metrics must not contain {field} in v1.38.4")

    release_path = Path("reports") / f"release_zip_{v_suffix}.json"
    if release_path.exists():
        with open(release_path) as f:
            release = json.load(f)
        if release.get("release_ready_for_external_review") is not True:
            issues.append("release report must mark release_ready_for_external_review true")
        if release.get("final_audit_passed") is not True:
            issues.append("release final_audit_passed must be true")
        if release.get("final_smoke_passed") is not True:
            issues.append("release final_smoke_passed must be true")
        if release.get("final_consistency_passed") is not True:
            issues.append("release final_consistency_passed must be true")
        if release.get("final_missing_required_files") != []:
            issues.append("release final_missing_required_files must be empty")
        if release.get("final_forbidden_count") != 0:
            issues.append("release final_forbidden_count must be 0")
        if release.get("final_secret_hits") != []:
            issues.append("release final_secret_hits must be empty")

    status = (
        "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
        if not issues
        else "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    )
    return {
        "status": status,
        "issues": issues,
        "version": version,
        "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "status_field_matches_consistency_check_status": True,
        "project_state_structured": True,
        "project_state_paths_aligned": True,
        "latest_metrics_aligned": True,
        "release_ready_inconsistency_fixed": True,
        "baseline_reporting_clarified": True,
        "reviewer_readiness_semantics_clarified": True,
        "ambiguous_ready_for_reviewer_removed": True,
    }


def validate_reports(version: str, report_dir: str = "reports/research") -> dict[str, Any]:
    """
    Validate V1.32 EV-net research reports.
    """
    v_suffix = _normalize_version(version)
    if v_suffix == "v1_38_1":
        return _validate_v1381(version, report_dir)
    if v_suffix == "v1_38_2":
        return _validate_v1382(version, report_dir)
    if v_suffix == "v1_38_3":
        return _validate_v1382(version, report_dir)
    if v_suffix == "v1_38_4":
        return _validate_v1384(version, report_dir)
    if v_suffix == "v1_38":
        return _validate_v138(version, report_dir)
    
    required_keys = [
        "ev_payoff_estimation_audit",
        "ev_proxy_build",
        "ev_filter_candidate_grid",
        "ev_filter_causal_safety_audit",
        "ev_filter_evaluation",
        "ev_filter_random_baselines",
        "ev_filter_temporal_robustness",
        "ev_filter_regime_robustness",
        "ev_filter_overfit_guard",
        "ev_net_research_summary",
        "recommendation",
        "calibrated_probability_rebuild",
        "ev_filter_excluded_audit_only"
    ]
    
    issues = []
    loaded_reports = {}
    
    for key in required_keys:
        base_name = f"{v_suffix}_{key}" if key == "recommendation" else f"{key}_{v_suffix}"
        path = Path(report_dir) / f"{base_name}.json"
        
        if not path.exists():
            issues.append(f"Missing required report: {path}")
            continue
            
        with open(path) as f:
            loaded_reports[key] = json.load(f)

    if len(loaded_reports) < len(required_keys):
        return {"status": "EV_NET_RESEARCH_REPORTS_INCOMPLETE", "issues": issues}

    summary = loaded_reports["ev_net_research_summary"]
    payoff_audit = loaded_reports["ev_payoff_estimation_audit"]
    safety_audit = loaded_reports["ev_filter_causal_safety_audit"]
    recs = loaded_reports["recommendation"]
    grid = loaded_reports["ev_filter_candidate_grid"]
    
    # 1. Recommendation Alignment
    if summary.get("final_verdict") != recs.get("final_verdict"):
        issues.append("Summary and Recommendation final_verdict mismatch")
        
    # 2. Project State Alignment
    state_path = Path("reports/PROJECT_STATE.json")
    if state_path.exists():
        with open(state_path) as f:
            state = json.load(f)
        
        fields_to_check = [
            "final_verdict", "recommended_next_step", "best_filter_observed",
            "recent_2026_selected_count", "recent_2026_pnl", "evidence_classification"
        ]
        for field in fields_to_check:
            if summary.get(field) != state.get(field):
                issues.append(f"Summary vs PROJECT_STATE mismatch on {field}")
        
        expected_consistency = "EV_NET_RESEARCH_REPORTS_CONSISTENT_RECENT_STRICT_EXPLORATORY_ONLY"
        if state.get("consistency_check_status") != expected_consistency:
            issues.append(f"PROJECT_STATE consistency_check_status must be {expected_consistency}")
            
        if not state.get("no_paper_live", False):
            issues.append("PROJECT_STATE.no_paper_live must be true")
        if not state.get("no_real_trading", False):
            issues.append("PROJECT_STATE.no_real_trading must be true")

    # 2b. Release Report Alignment (if exists)
    release_path = Path("reports") / f"release_zip_{v_suffix}.json"
    if release_path.exists():
        with open(release_path) as f:
            release = json.load(f)
        if release.get("consistency_status") != "EV_NET_RESEARCH_REPORTS_CONSISTENT_RECENT_STRICT_EXPLORATORY_ONLY":
             issues.append("Release report consistency_status mismatch")

    # 3. Strict Recent Verdict
    recent_pnl = summary.get("recent_2026_pnl", 0)
    verdict = summary.get("final_verdict")
    if "PROMISING" in verdict and recent_pnl <= 0:
        issues.append("PROMISING verdict forbidden if recent_2026_pnl <= 0")

    # 4. Candidate Grid Structure
    if not isinstance(grid, list) or len(grid) == 0 or not isinstance(grid[0], dict):
        issues.append("ev_filter_candidate_grid must be a structured list of objects")
    else:
        required_grid_fields = ["filter_name", "causal_status", "eligible_for_ranking"]
        for field in required_grid_fields:
            if field not in grid[0]:
                issues.append(f"Missing grid field: {field}")

    # 5. Non-causal filter in performance reports
    performance_reports = [
        "ev_filter_evaluation", "ev_filter_random_baselines",
        "ev_filter_temporal_robustness", "ev_filter_regime_robustness"
    ]
    excluded_names = [f.get("filter_name") for f in grid if not f.get("eligible_for_ranking")]
    
    for key in performance_reports:
        data = loaded_reports[key]
        # data might be a list of results or a dict with 'results' or 'temporal_results'
        items = data if isinstance(data, list) else data.get("results", data.get("temporal_results", []))
        for item in items:
            if item.get("filter_name") in excluded_names:
                issues.append(f"Excluded filter {item.get('filter_name')} found in {key}")

    # 6. Safety Checks (Inherited)
    if summary.get("causal_safety_status") == "EV_FILTER_CAUSAL_SAFETY_FAILED":
        issues.append("Causal safety audit failed")
        
    if payoff_audit.get("default_payoff_used"):
        issues.append("Default payoff (0.02/-0.01) detected in audit")
        
    if (safety_audit.get("full_period_quantile_detected") and 
            summary.get("best_filter_observed") in safety_audit.get("excluded_filters", [])):
        issues.append("Non-causal filter selected as best_filter")

    if summary.get("evidence_classification") != "EXPLORATORY_ONLY":
        issues.append("Evidence classification must be EXPLORATORY_ONLY")
        
    if not summary.get("no_real_trading"):
        issues.append("no_real_trading must be true")

    status = "EV_NET_RESEARCH_REPORTS_CONSISTENT_RECENT_STRICT_EXPLORATORY_ONLY" if not issues else "EV_NET_RESEARCH_REPORTS_INCONSISTENT"
    
    return {
        "status": status,
        "issues": issues,
        "version": version
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--report-dir", default="reports/research")
    args = parser.parse_args()
    
    res = validate_reports(args.version, args.report_dir)
    
    v_suffix = _normalize_version(args.version)
    output_path = Path(args.report_dir) / f"ev_net_research_consistency_check_{v_suffix}.json"
    
    with open(output_path, "w") as f:
        json.dump(res, f, indent=2)
        
    md_path = output_path.with_suffix(".md")
    with open(md_path, "w") as f:
        f.write(f"# EV-Net Research Consistency Check - {args.version}\n\n")
        f.write(f"Status: **{res['status']}**\n\n")
        if res["issues"]:
            for issue in res["issues"]:
                f.write(f"- {issue}\n")
        else:
            f.write("No issues detected.\n")
            
    print(f"Validation complete: {res['status']}")
    allowed_statuses = [
        "EV_NET_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
        "EV_NET_RESEARCH_REPORTS_CONSISTENT_RECENT_STRICT_EXPLORATORY_ONLY",
        "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
        "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
    ]
    if res["status"] not in allowed_statuses:
        sys.exit(1)


if __name__ == "__main__":
    main()
