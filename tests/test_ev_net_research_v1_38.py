from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

from galapagos.research.ev_net_research.canonical_ev_feature_rebuilder import (
    rebuild_canonical_ev_features,
)
from galapagos.research.ev_net_research.canonical_input_guard import (
    audit_canonical_input_guard,
)
from galapagos.research.ev_net_research.recommendation_engine import (
    build_v1_38_1_baseline_interpretation,
    generate_v1_38_recommendation,
    generate_v1_38_1_recommendation,
    generate_v1_38_2_recommendation,
    generate_v1_38_3_recommendation,
    generate_v1_38_4_recommendation,
)


def _load_validate_reports():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "validate_ev_net_research_reports.py"
    spec = importlib.util.spec_from_file_location("validate_ev_net_research_reports", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_reports


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _base_summary() -> dict:
    return {
        "version": "V1.38",
        "canonical_base_version": "V1.37.2",
        "input_guard_status": "EV_NET_CANONICAL_INPUT_GUARD_PASSED",
        "selection_outcome_split_status": "PREDICTION_FRAME_INTEGRITY_PASSED",
        "selection_dataset_rows": 171648,
        "outcome_dataset_rows": 171648,
        "opportunity_index_rows": 171648,
        "raw_prediction_rows": 171648,
        "raw_prediction_rows_2026": 24360,
        "ev_feature_rebuild_status": "EV_NET_FEATURE_REBUILD_COMPLETE",
        "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED",
        "evaluation_status": "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED",
        "random_baseline_status": "EV_NET_CANONICAL_RANDOM_BASELINES_COMPLETED",
        "temporal_robustness_status": "EV_NET_CANONICAL_TEMPORAL_ROBUSTNESS_COMPLETED",
        "regime_robustness_status": "REGIME_ANALYSIS_COMPLETED",
        "overfit_guard_status": "EV_NET_CANONICAL_OVERFIT_GUARD_COMPLETED_EXPLORATORY_ONLY",
        "best_filter_observed": "filter_ev_gt_cost_buffer",
        "best_filter_selection_status": "BEST_FILTER_EVALUATED",
        "best_filter_selected_count": 122,
        "best_filter_selected_count_2026": 24,
        "best_filter_mean_net_pnl": 0.018,
        "best_filter_2026_mean_net_pnl": 0.004,
        "beats_monthly_random_p95": True,
        "active_windows_count": 4,
        "recent_window_status": "TEMPORALLY_ACTIVE",
        "selected_count_total": 122,
        "filters_tested_count": 5,
        "eligible_filters_count": 4,
        "excluded_filters_count": 1,
        "causal_filter_count": 4,
        "non_causal_filter_count": 1,
        "default_payoff_used": False,
        "fallback_probability_used": False,
        "artificial_probability_threshold_used": False,
        "evidence_classification": "EXPLORATORY_ONLY",
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_money_deployment": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "selection_frame_forbidden_columns": [],
        "selection_frame_status": "PREDICTION_FRAME_SELECTION_OK",
        "outcome_frame_status": "OUTCOME_FRAME_AVAILABLE",
        "rows_blocked_by_warmup_count": 100,
        "final_verdict": "EV_NET_CANONICAL_RESEARCH_PROMISING_BUT_UNVALIDATED",
        "recommended_next_step": "harden canonical EV-net robustness and prepare a preregistration candidate only after additional diagnostics",
        "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
        "causal_safety_status": "EV_FILTER_CAUSAL_SAFETY_PASSED_WITH_EXCLUSIONS",
    }


def _base_summary_v1381() -> dict:
    summary = _base_summary()
    summary.update(
        {
            "version": "V1.38.1",
            "previous_base": "V1.38",
            "purpose": "EV-net canonical research state/release consistency fix",
            "canonical_base_version": "V1.37.2",
            "input_guard_status": "EV_NET_CANONICAL_INPUT_GUARD_PASSED",
            "selection_outcome_split_status": "PREDICTION_FRAME_INTEGRITY_PASSED",
            "selection_dataset_rows": 171648,
            "outcome_dataset_rows": 171648,
            "opportunity_index_rows": 171648,
            "raw_prediction_rows": 171648,
            "raw_prediction_rows_2026": 24360,
            "ev_feature_rebuild_status": "EV_NET_FEATURE_REBUILD_COMPLETE",
            "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED",
            "evaluation_status": "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED",
            "random_baseline_status": "EV_NET_CANONICAL_RANDOM_BASELINES_COMPLETED",
            "temporal_robustness_status": "EV_NET_CANONICAL_TEMPORAL_ROBUSTNESS_COMPLETED",
            "regime_robustness_status": "REGIME_ANALYSIS_COMPLETED",
            "overfit_guard_status": "EV_NET_CANONICAL_OVERFIT_GUARD_COMPLETED_EXPLORATORY_ONLY",
            "best_filter_observed": "filter_ev_gt_0",
            "best_filter_selection_status": "BEST_FILTER_EVALUATED",
            "best_filter_selected_count": 129527,
            "best_filter_selected_count_2026": 19497,
            "best_filter_mean_net_pnl": -2.6852081489793344e-05,
            "best_filter_2026_mean_net_pnl": -0.00321872050730674,
            "beats_global_random_p95": False,
            "beats_monthly_random_p95": True,
            "active_windows_count": 4,
            "recent_window_status": "RECENT_WINDOW_NEGATIVE",
            "selected_count_total": 253106,
            "filters_tested_count": 5,
            "eligible_filters_count": 4,
            "excluded_filters_count": 1,
            "causal_filter_count": 4,
            "non_causal_filter_count": 1,
            "default_payoff_used": False,
            "fallback_probability_used": False,
            "artificial_probability_threshold_used": False,
            "evidence_classification": "EXPLORATORY_ONLY",
            "no_strategy_validated": True,
            "no_preregistration_yet": True,
            "no_paper_live": True,
            "no_money_deployment": True,
            "no_real_trading": True,
            "holdout_executed": False,
            "codex_cli_called": False,
            "selection_frame_forbidden_columns": [],
            "selection_frame_status": "POINT_IN_TIME_AUDIT_HAS_UNKNOWN_COLUMNS",
            "outcome_frame_status": "OUTCOME_FRAME_AVAILABLE",
            "rows_blocked_by_warmup_count": 37212,
            "final_verdict": "EV_NET_CANONICAL_RESEARCH_RECENT_WINDOW_NEGATIVE",
            "recommended_next_step": "diagnose canonical EV-net 2026 degradation before preregistration",
            "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
            "causal_safety_status": "EV_FILTER_CAUSAL_SAFETY_PASSED_WITH_EXCLUSIONS",
            "release_ready_for_external_review": True,
            "project_state_structured": True,
            "baseline_reporting_status": "EV_NET_BASELINE_REPORTING_CLARIFIED",
            "recommendation_artifact_json_path": "reports/research/v1_38_1_recommendation.json",
            "recommendation_artifact_md_path": "reports/research/v1_38_1_recommendation.md",
            "beats_global_random_p95": False,
            "top_global_pnl_filter": "filter_ev_top_quantile_causal",
            "top_global_pnl_filter_mean_net_pnl": 0.006775835866973116,
            "top_global_pnl_filter_recent_2026_selected_count": 0,
            "top_global_pnl_filter_recent_status": "RECENT_WINDOW_NO_SIGNALS",
            "previous_v1_38_release_ready_inconsistency_fixed": True,
        }
    )
    return summary


def _write_v1381_reports(root: Path, overrides: dict[str, dict] | None = None) -> dict[str, dict]:
    overrides = overrides or {}
    summary = _base_summary_v1381()
    summary.update(overrides.get("summary", {}))
    recommendation = generate_v1_38_1_recommendation(summary)
    baseline_interp = build_v1_38_1_baseline_interpretation(summary)
    reports = {
        "ev_net_canonical_input_guard": {
            "canonical_base_version": "V1.37.2",
            "guard_status": "EV_NET_CANONICAL_INPUT_GUARD_PASSED",
            "real_data_enforced": True,
            "mock_data_detected": False,
            "raw_prediction_rows": 171648,
            "raw_prediction_rows_2026": 24360,
            "selection_dataset_rows": 171648,
            "selection_dataset_rows_2026": 24360,
            "outcome_dataset_rows": 171648,
            "outcome_dataset_rows_2026": 24360,
            "opportunity_index_rows": 171648,
            "opportunity_index_rows_2026": 24360,
        },
        "ev_net_feature_rebuild": {
            "selection_outcome_split_status": "PREDICTION_FRAME_INTEGRITY_PASSED",
            "selection_frame_forbidden_columns": [],
            "default_payoff_used": False,
            "fallback_probability_used": False,
            "artificial_probability_threshold_used": False,
            "ev_feature_rebuild_status": "EV_NET_FEATURE_REBUILD_COMPLETE",
        },
        "ev_net_filter_grid": {
            "filters_tested": [
                {"filter_name": "filter_ev_gt_cost_buffer", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_gt_0", "causal_status": "CAUSAL"},
                {"filter_name": "filter_prob_65_ev_pos", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_top_quantile_causal", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_top_quantile_non_causal", "causal_status": "RETROSPECTIVE_ONLY_FULL_PERIOD_QUANTILE"},
            ],
            "eligible_filters": [
                "filter_ev_gt_cost_buffer",
                "filter_ev_gt_0",
                "filter_prob_65_ev_pos",
                "filter_ev_top_quantile_causal",
            ],
            "excluded_filters": ["filter_ev_top_quantile_non_causal"],
            "exclusion_reasons": {"filter_ev_top_quantile_non_causal": "full_period_quantile_non_causal"},
            "causal_filter_count": 4,
            "non_causal_filter_count": 1,
            "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED",
        },
        "ev_net_filter_evaluation": {
            "status": "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED",
            "results": [
                {"filter_name": "filter_ev_gt_0", "selected_count": 129527},
                {"filter_name": "filter_ev_gt_cost_buffer", "selected_count": 122},
                {"filter_name": "filter_prob_65_ev_pos", "selected_count": 0},
                {"filter_name": "filter_ev_top_quantile_causal", "selected_count": 10774},
            ],
        },
        "ev_net_random_baselines": {
            "status": "EV_NET_CANONICAL_RANDOM_BASELINES_COMPLETED",
            "results": [
                {"filter_name": "filter_ev_gt_0", "baseline_type": "GLOBAL_SAME_COUNT", "beats_random_p95": False},
                {"filter_name": "filter_ev_gt_0", "baseline_type": "MONTHLY_COUNT_PRESERVING", "beats_random_p95": True},
                {"filter_name": "filter_ev_top_quantile_causal", "baseline_type": "GLOBAL_SAME_COUNT", "beats_random_p95": True},
                {"filter_name": "filter_ev_top_quantile_causal", "baseline_type": "MONTHLY_COUNT_PRESERVING", "beats_random_p95": True},
            ],
        },
        "ev_net_temporal_robustness": {
            "status": "EV_NET_CANONICAL_TEMPORAL_ROBUSTNESS_COMPLETED",
            "temporal_results": [],
            "summary_by_filter": {
                "filter_ev_gt_0": {
                    "active_windows_count": 4,
                    "recent_2026_selected_count": 19497,
                    "recent_2026_pnl": -0.00321872050730674,
                    "activity_status": "RECENT_WINDOW_NEGATIVE",
                }
            },
        },
        "ev_net_regime_robustness": {
            "status": "REGIME_ANALYSIS_COMPLETED",
            "results": [],
        },
        "ev_net_overfit_guard": {
            "evidence_classification": "EXPLORATORY_ONLY",
            "preregistration_allowed": False,
            "paper_live_allowed": False,
        },
        "ev_net_baseline_interpretation": baseline_interp,
        "ev_net_research_summary": summary,
        "ev_net_research_consistency_check": {
            "status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
            "issues": [],
            "version": "V1.38.1",
            "project_state_structured": True,
            "project_state_paths_aligned": True,
            "latest_metrics_aligned": True,
            "release_ready_inconsistency_fixed": True,
            "baseline_reporting_clarified": True,
        },
        "recommendation": recommendation,
    }

    for key, payload in overrides.items():
        if key in reports:
            reports[key].update(payload)
        elif key == "summary":
            reports["ev_net_research_summary"].update(payload)

    report_dir = root / "reports" / "research"
    for name, payload in reports.items():
        filename = f"{name}_v1_38_1.json" if name != "recommendation" else "v1_38_1_recommendation.json"
        _write_json(report_dir / filename, payload)
        md_name = filename.replace(".json", ".md")
        (report_dir / md_name).write_text("# test\n", encoding="utf-8")

    release_payload = {
        "version": "V1.38.1",
        "final_zip_created": True,
        "final_zip_path": "projet-galapagos-v1.38.1-clean.zip",
        "final_zip_contains_audit_reports": True,
        "final_zip_contains_smoke_reports": True,
        "final_audit_passed": True,
        "final_smoke_passed": True,
        "final_consistency_passed": True,
        "final_missing_required_files": [],
        "final_forbidden_count": 0,
        "final_secret_hits": [],
        "release_ready_for_external_review": True,
        "consistency_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
    }
    _write_json(root / "reports" / "release_zip_v1_38_1.json", release_payload)
    (root / "reports" / "release_zip_v1_38_1.md").write_text("# release\n", encoding="utf-8")

    _write_json(root / "reports" / "PROJECT_STATE.json", {
        "version": "V1.38.1",
        "previous_base": "V1.38",
        "purpose": "EV-net canonical research state/release consistency fix",
        "final_verdict": summary["final_verdict"],
        "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
        "evidence_classification": "EXPLORATORY_ONLY",
        "recommended_next_step": summary["recommended_next_step"],
        "release_ready_for_external_review": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "canonical_base_version": "V1.37.2",
        "project_state_structured": True,
        "baseline_reporting_status": "EV_NET_BASELINE_REPORTING_CLARIFIED",
        "recommendation_artifact_json_path": "reports/research/v1_38_1_recommendation.json",
        "recommendation_artifact_md_path": "reports/research/v1_38_1_recommendation.md",
        "canonical_universe_context": {
            "canonical_base_version": "V1.37.2",
            "canonical_opportunity_rows": 171648,
            "canonical_opportunity_rows_2026": 24360,
            "selection_dataset_rows": 171648,
            "outcome_dataset_rows": 171648,
            "opportunity_index_rows": 171648,
            "ev_feature_status": "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
            "cost_policy_status": "COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
            "no_filter_applied_to_canonical_opportunity_universe": True,
        },
        "v1_38_research_context": {
            "ev_feature_rebuild_status": "EV_NET_FEATURE_REBUILD_COMPLETE",
            "ev_ready_rows": 134436,
            "ev_ready_rows_2026": 24360,
            "rows_blocked_by_warmup_count": 37212,
            "default_payoff_used": False,
            "fallback_probability_used": False,
            "artificial_probability_threshold_used": False,
            "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED",
            "evaluation_status": "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED",
            "best_filter_observed": "filter_ev_gt_0",
            "best_filter_mean_net_pnl": -2.6852081489793344e-05,
            "best_filter_2026_mean_net_pnl": -0.00321872050730674,
        },
    },)
    (root / "reports" / "PROJECT_STATE.md").write_text("# state\n", encoding="utf-8")
    _write_json(root / "reports" / "current" / "latest_metrics.json", summary)
    (root / "reports" / "current" / "latest_summary.md").write_text("# summary\n", encoding="utf-8")

    return reports


def _base_summary_v1382() -> dict:
    summary = _base_summary_v1381()
    summary.update(
        {
            "version": "V1.38.2",
            "previous_base": "V1.38.1",
            "purpose": "EV-net consistency field and reviewer readiness semantics fix",
            "release_ready_for_external_review": True,
            "project_state_structured": True,
            "baseline_reporting_status": "EV_NET_BASELINE_REPORTING_CLARIFIED",
            "recommendation_artifact_json_path": "reports/research/v1_38_2_recommendation.json",
            "recommendation_artifact_md_path": "reports/research/v1_38_2_recommendation.md",
            "ready_for_reviewer": False,
            "ready_for_reviewer_scope": "strategy_validation",
            "ready_for_reviewer_is_release_ready": False,
            "strategy_reviewer_ready": False,
            "strategy_reviewer_ready_reason": "recent 2026 window negative and no strategy validated",
            "paper_live_ready": False,
            "preregistration_ready": False,
            "money_deployment_ready": False,
            "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
            "previous_v1_38_release_ready_inconsistency_fixed": True,
            "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
            "selected_count_total": 253106,
        }
    )
    return summary


def _base_summary_v1383() -> dict:
    summary = _base_summary_v1382()
    summary.update(
        {
            "version": "V1.38.3",
            "previous_base": "V1.38.2",
            "purpose": "EV-net final consistency field and ambiguous reviewer flag removal",
            "release_ready_for_external_review": True,
            "project_state_structured": True,
            "baseline_reporting_status": "EV_NET_BASELINE_REPORTING_CLARIFIED",
            "recommendation_artifact_json_path": "reports/research/v1_38_3_recommendation.json",
            "recommendation_artifact_md_path": "reports/research/v1_38_3_recommendation.md",
            "strategy_reviewer_ready": False,
            "strategy_reviewer_ready_reason": "recent 2026 window negative and no strategy validated",
            "paper_live_ready": False,
            "preregistration_ready": False,
            "money_deployment_ready": False,
            "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
            "previous_v1_38_release_ready_inconsistency_fixed": True,
            "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
        }
    )
    summary.pop("ready_for_reviewer", None)
    summary.pop("ready_for_reviewer_scope", None)
    summary.pop("ready_for_reviewer_is_release_ready", None)
    return summary


def _write_v1383_reports(root: Path, overrides: dict[str, dict] | None = None) -> dict[str, dict]:
    overrides = overrides or {}
    summary = _base_summary_v1383()
    summary.update(overrides.get("summary", {}))
    recommendation = generate_v1_38_3_recommendation(summary)
    baseline_interp = build_v1_38_1_baseline_interpretation(summary)
    reports = {
        "ev_net_canonical_input_guard": {
            "canonical_base_version": "V1.37.2",
            "guard_status": "EV_NET_CANONICAL_INPUT_GUARD_PASSED",
            "real_data_enforced": True,
            "mock_data_detected": False,
            "raw_prediction_rows": 171648,
            "raw_prediction_rows_2026": 24360,
            "selection_dataset_rows": 171648,
            "selection_dataset_rows_2026": 24360,
            "outcome_dataset_rows": 171648,
            "outcome_dataset_rows_2026": 24360,
            "opportunity_index_rows": 171648,
            "opportunity_index_rows_2026": 24360,
        },
        "ev_net_feature_rebuild": {
            "selection_outcome_split_status": "PREDICTION_FRAME_INTEGRITY_PASSED",
            "selection_frame_forbidden_columns": [],
            "default_payoff_used": False,
            "fallback_probability_used": False,
            "artificial_probability_threshold_used": False,
            "ev_feature_rebuild_status": "EV_NET_FEATURE_REBUILD_COMPLETE",
        },
        "ev_net_filter_grid": {
            "filters_tested": [
                {"filter_name": "filter_ev_gt_cost_buffer", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_gt_0", "causal_status": "CAUSAL"},
                {"filter_name": "filter_prob_65_ev_pos", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_top_quantile_causal", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_top_quantile_non_causal", "causal_status": "RETROSPECTIVE_ONLY_FULL_PERIOD_QUANTILE"},
            ],
            "eligible_filters": [
                "filter_ev_gt_cost_buffer",
                "filter_ev_gt_0",
                "filter_prob_65_ev_pos",
                "filter_ev_top_quantile_causal",
            ],
            "excluded_filters": ["filter_ev_top_quantile_non_causal"],
            "exclusion_reasons": {"filter_ev_top_quantile_non_causal": "full_period_quantile_non_causal"},
            "causal_filter_count": 4,
            "non_causal_filter_count": 1,
            "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED",
        },
        "ev_net_filter_evaluation": {
            "status": "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED",
            "results": [
                {"filter_name": "filter_ev_gt_0", "selected_count": 129527},
            ],
        },
        "ev_net_random_baselines": {
            "status": "EV_NET_CANONICAL_RANDOM_BASELINES_COMPLETED",
            "results": [
                {"filter_name": "filter_ev_gt_0", "baseline_type": "GLOBAL_SAME_COUNT", "beats_random_p95": False},
                {"filter_name": "filter_ev_gt_0", "baseline_type": "MONTHLY_COUNT_PRESERVING", "beats_random_p95": True},
            ],
        },
        "ev_net_temporal_robustness": {
            "status": "EV_NET_CANONICAL_TEMPORAL_ROBUSTNESS_COMPLETED",
            "temporal_results": [],
            "summary_by_filter": {
                "filter_ev_gt_0": {
                    "active_windows_count": 4,
                    "recent_2026_selected_count": 19497,
                    "recent_2026_pnl": -0.00321872050730674,
                    "activity_status": "RECENT_WINDOW_NEGATIVE",
                }
            },
        },
        "ev_net_regime_robustness": {
            "status": "REGIME_ANALYSIS_COMPLETED",
            "results": [],
        },
        "ev_net_overfit_guard": {
            "evidence_classification": "EXPLORATORY_ONLY",
            "preregistration_allowed": False,
            "paper_live_allowed": False,
        },
        "ev_net_baseline_interpretation": baseline_interp,
        "ev_net_research_summary": summary,
        "ev_net_research_consistency_check": {
            "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
            "issues": [],
            "version": "V1.38.3",
            "project_state_structured": True,
            "project_state_paths_aligned": True,
            "latest_metrics_aligned": True,
            "release_ready_inconsistency_fixed": True,
            "baseline_reporting_clarified": True,
            "legacy_status_field_removed_or_mirrored": True,
            "reviewer_readiness_semantics_clarified": True,
            "ambiguous_ready_for_reviewer_removed": True,
            "status_field_present": False,
            "status_field_matches_consistency_check_status": True,
        },
        "recommendation": recommendation,
    }

    for key, payload in overrides.items():
        if key in reports:
            reports[key].update(payload)
        elif key == "summary":
            reports["ev_net_research_summary"].update(payload)

    report_dir = root / "reports" / "research"
    for name, payload in reports.items():
        filename = f"{name}_v1_38_3.json" if name != "recommendation" else "v1_38_3_recommendation.json"
        _write_json(report_dir / filename, payload)
        md_name = filename.replace(".json", ".md")
        (report_dir / md_name).write_text("# test\n", encoding="utf-8")

    release_payload = {
        "version": "V1.38.3",
        "final_zip_created": True,
        "final_zip_path": "projet-galapagos-v1.38.3-clean.zip",
        "final_zip_contains_audit_reports": True,
        "final_zip_contains_smoke_reports": True,
        "final_audit_passed": True,
        "final_smoke_passed": True,
        "final_consistency_passed": True,
        "final_missing_required_files": [],
        "final_forbidden_count": 0,
        "final_secret_hits": [],
        "release_ready_for_external_review": True,
        "consistency_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
    }
    _write_json(root / "reports" / "release_zip_v1_38_3.json", release_payload)
    (root / "reports" / "release_zip_v1_38_3.md").write_text("# release\n", encoding="utf-8")

    _write_json(root / "reports" / "PROJECT_STATE.json", {
        "version": "V1.38.3",
        "previous_base": "V1.38.2",
        "purpose": "EV-net final consistency field and ambiguous reviewer flag removal",
        "final_verdict": summary["final_verdict"],
        "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
        "evidence_classification": "EXPLORATORY_ONLY",
        "recommended_next_step": summary["recommended_next_step"],
        "release_ready_for_external_review": True,
        "strategy_reviewer_ready": False,
        "paper_live_ready": False,
        "preregistration_ready": False,
        "money_deployment_ready": False,
        "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "ambiguous_ready_for_reviewer_removed": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "canonical_base_version": "V1.37.2",
        "project_state_structured": True,
        "baseline_reporting_status": "EV_NET_BASELINE_REPORTING_CLARIFIED",
        "recommendation_artifact_json_path": "reports/research/v1_38_3_recommendation.json",
        "recommendation_artifact_md_path": "reports/research/v1_38_3_recommendation.md",
        "canonical_universe_context": {
            "canonical_base_version": "V1.37.2",
            "canonical_opportunity_rows": 171648,
            "canonical_opportunity_rows_2026": 24360,
            "selection_dataset_rows": 171648,
            "outcome_dataset_rows": 171648,
            "opportunity_index_rows": 171648,
            "ev_feature_status": "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
            "cost_policy_status": "COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
            "no_filter_applied_to_canonical_opportunity_universe": True,
        },
        "v1_38_research_context": {
            "ev_feature_rebuild_status": "EV_NET_FEATURE_REBUILD_COMPLETE",
            "ev_ready_rows": 134436,
            "ev_ready_rows_2026": 24360,
            "rows_blocked_by_warmup_count": 37212,
            "default_payoff_used": False,
            "fallback_probability_used": False,
            "artificial_probability_threshold_used": False,
            "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED",
            "evaluation_status": "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED",
            "best_filter_observed": "filter_ev_gt_0",
            "best_filter_mean_net_pnl": -2.6852081489793344e-05,
            "best_filter_2026_mean_net_pnl": -0.00321872050730674,
        },
    },)
    (root / "reports" / "PROJECT_STATE.md").write_text("# state\n", encoding="utf-8")
    metrics = summary.copy()
    metrics.pop("ready_for_reviewer", None)
    metrics.pop("ready_for_reviewer_scope", None)
    metrics.pop("ready_for_reviewer_is_release_ready", None)
    _write_json(root / "reports" / "current" / "latest_metrics.json", metrics)
    (root / "reports" / "current" / "latest_summary.md").write_text("# summary\n", encoding="utf-8")

    return reports


def _write_v1382_reports(root: Path, overrides: dict[str, dict] | None = None) -> dict[str, dict]:
    overrides = overrides or {}
    summary = _base_summary_v1382()
    summary.update(overrides.get("summary", {}))
    recommendation = generate_v1_38_2_recommendation(summary)
    baseline_interp = build_v1_38_1_baseline_interpretation(summary)
    reports = {
        "ev_net_canonical_input_guard": {
            "canonical_base_version": "V1.37.2",
            "guard_status": "EV_NET_CANONICAL_INPUT_GUARD_PASSED",
            "real_data_enforced": True,
            "mock_data_detected": False,
            "raw_prediction_rows": 171648,
            "raw_prediction_rows_2026": 24360,
            "selection_dataset_rows": 171648,
            "selection_dataset_rows_2026": 24360,
            "outcome_dataset_rows": 171648,
            "outcome_dataset_rows_2026": 24360,
            "opportunity_index_rows": 171648,
            "opportunity_index_rows_2026": 24360,
        },
        "ev_net_feature_rebuild": {
            "selection_outcome_split_status": "PREDICTION_FRAME_INTEGRITY_PASSED",
            "selection_frame_forbidden_columns": [],
            "default_payoff_used": False,
            "fallback_probability_used": False,
            "artificial_probability_threshold_used": False,
            "ev_feature_rebuild_status": "EV_NET_FEATURE_REBUILD_COMPLETE",
        },
        "ev_net_filter_grid": {
            "filters_tested": [
                {"filter_name": "filter_ev_gt_cost_buffer", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_gt_0", "causal_status": "CAUSAL"},
                {"filter_name": "filter_prob_65_ev_pos", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_top_quantile_causal", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_top_quantile_non_causal", "causal_status": "RETROSPECTIVE_ONLY_FULL_PERIOD_QUANTILE"},
            ],
            "eligible_filters": [
                "filter_ev_gt_cost_buffer",
                "filter_ev_gt_0",
                "filter_prob_65_ev_pos",
                "filter_ev_top_quantile_causal",
            ],
            "excluded_filters": ["filter_ev_top_quantile_non_causal"],
            "exclusion_reasons": {"filter_ev_top_quantile_non_causal": "full_period_quantile_non_causal"},
            "causal_filter_count": 4,
            "non_causal_filter_count": 1,
            "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED",
        },
        "ev_net_filter_evaluation": {
            "status": "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED",
            "results": [
                {"filter_name": "filter_ev_gt_0", "selected_count": 129527},
            ],
        },
        "ev_net_random_baselines": {
            "status": "EV_NET_CANONICAL_RANDOM_BASELINES_COMPLETED",
            "results": [
                {"filter_name": "filter_ev_gt_0", "baseline_type": "GLOBAL_SAME_COUNT", "beats_random_p95": False},
                {"filter_name": "filter_ev_gt_0", "baseline_type": "MONTHLY_COUNT_PRESERVING", "beats_random_p95": True},
            ],
        },
        "ev_net_temporal_robustness": {
            "status": "EV_NET_CANONICAL_TEMPORAL_ROBUSTNESS_COMPLETED",
            "temporal_results": [],
            "summary_by_filter": {
                "filter_ev_gt_0": {
                    "active_windows_count": 4,
                    "recent_2026_selected_count": 19497,
                    "recent_2026_pnl": -0.00321872050730674,
                    "activity_status": "RECENT_WINDOW_NEGATIVE",
                }
            },
        },
        "ev_net_regime_robustness": {
            "status": "REGIME_ANALYSIS_COMPLETED",
            "results": [],
        },
        "ev_net_overfit_guard": {
            "evidence_classification": "EXPLORATORY_ONLY",
            "preregistration_allowed": False,
            "paper_live_allowed": False,
        },
        "ev_net_baseline_interpretation": baseline_interp,
        "ev_net_reviewer_readiness_semantics": {
            "release_ready_for_external_review": True,
            "strategy_reviewer_ready": False,
            "strategy_reviewer_ready_reason": "recent 2026 window negative and no strategy validated",
            "paper_live_ready": False,
            "preregistration_ready": False,
            "money_deployment_ready": False,
            "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
        },
        "ev_net_research_summary": summary,
        "ev_net_research_consistency_check": {
            "status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
            "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
            "issues": [],
            "version": "V1.38.2",
            "project_state_structured": True,
            "project_state_paths_aligned": True,
            "latest_metrics_aligned": True,
            "release_ready_inconsistency_fixed": True,
            "baseline_reporting_clarified": True,
            "legacy_status_field_removed_or_mirrored": True,
            "reviewer_readiness_semantics_clarified": True,
        },
        "recommendation": recommendation,
    }

    for key, payload in overrides.items():
        if key in reports:
            reports[key].update(payload)
        elif key == "summary":
            reports["ev_net_research_summary"].update(payload)

    report_dir = root / "reports" / "research"
    for name, payload in reports.items():
        filename = f"{name}_v1_38_2.json" if name != "recommendation" else "v1_38_2_recommendation.json"
        _write_json(report_dir / filename, payload)
        md_name = filename.replace(".json", ".md")
        (report_dir / md_name).write_text("# test\n", encoding="utf-8")

    release_payload = {
        "version": "V1.38.2",
        "final_zip_created": True,
        "final_zip_path": "projet-galapagos-v1.38.2-clean.zip",
        "final_zip_contains_audit_reports": True,
        "final_zip_contains_smoke_reports": True,
        "final_audit_passed": True,
        "final_smoke_passed": True,
        "final_consistency_passed": True,
        "final_missing_required_files": [],
        "final_forbidden_count": 0,
        "final_secret_hits": [],
        "release_ready_for_external_review": True,
        "consistency_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
    }
    _write_json(root / "reports" / "release_zip_v1_38_2.json", release_payload)
    (root / "reports" / "release_zip_v1_38_2.md").write_text("# release\n", encoding="utf-8")

    _write_json(root / "reports" / "PROJECT_STATE.json", {
        "version": "V1.38.2",
        "previous_base": "V1.38.1",
        "purpose": "EV-net consistency field and reviewer readiness semantics fix",
        "final_verdict": summary["final_verdict"],
        "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
        "evidence_classification": "EXPLORATORY_ONLY",
        "recommended_next_step": summary["recommended_next_step"],
        "release_ready_for_external_review": True,
        "ready_for_reviewer": False,
        "ready_for_reviewer_scope": "strategy_validation",
        "ready_for_reviewer_is_release_ready": False,
        "strategy_reviewer_ready": False,
        "paper_live_ready": False,
        "preregistration_ready": False,
        "money_deployment_ready": False,
        "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
        "previous_v1_38_release_ready_inconsistency_fixed": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "canonical_base_version": "V1.37.2",
        "project_state_structured": True,
        "baseline_reporting_status": "EV_NET_BASELINE_REPORTING_CLARIFIED",
        "recommendation_artifact_json_path": "reports/research/v1_38_2_recommendation.json",
        "recommendation_artifact_md_path": "reports/research/v1_38_2_recommendation.md",
        "canonical_universe_context": {
            "canonical_base_version": "V1.37.2",
            "canonical_opportunity_rows": 171648,
            "canonical_opportunity_rows_2026": 24360,
            "selection_dataset_rows": 171648,
            "outcome_dataset_rows": 171648,
            "opportunity_index_rows": 171648,
            "ev_feature_status": "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
            "cost_policy_status": "COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
            "no_filter_applied_to_canonical_opportunity_universe": True,
        },
        "v1_38_research_context": {
            "ev_feature_rebuild_status": "EV_NET_FEATURE_REBUILD_COMPLETE",
            "ev_ready_rows": 134436,
            "ev_ready_rows_2026": 24360,
            "rows_blocked_by_warmup_count": 37212,
            "default_payoff_used": False,
            "fallback_probability_used": False,
            "artificial_probability_threshold_used": False,
            "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED",
            "evaluation_status": "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED",
            "best_filter_observed": "filter_ev_gt_0",
            "best_filter_mean_net_pnl": -2.6852081489793344e-05,
            "best_filter_2026_mean_net_pnl": -0.00321872050730674,
        },
    },)
    (root / "reports" / "PROJECT_STATE.md").write_text("# state\n", encoding="utf-8")
    _write_json(root / "reports" / "current" / "latest_metrics.json", summary)
    (root / "reports" / "current" / "latest_summary.md").write_text("# summary\n", encoding="utf-8")

    return reports


def _base_summary_v1384() -> dict:
    summary = _base_summary_v1383()
    summary.update(
        {
            "version": "V1.38.4",
            "previous_base": "V1.38.3",
            "purpose": "EV-net consistency check status field self-consistency fix",
            "release_ready_for_external_review": True,
            "project_state_structured": True,
            "baseline_reporting_status": "EV_NET_BASELINE_REPORTING_CLARIFIED",
            "recommendation_artifact_json_path": "reports/research/v1_38_4_recommendation.json",
            "recommendation_artifact_md_path": "reports/research/v1_38_4_recommendation.md",
            "status_field_policy": "REMOVED",
            "status_field_present": False,
            "strategy_reviewer_ready": False,
            "strategy_reviewer_ready_reason": "recent 2026 window negative and no strategy validated",
            "paper_live_ready": False,
            "preregistration_ready": False,
            "money_deployment_ready": False,
            "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
            "previous_v1_38_release_ready_inconsistency_fixed": True,
            "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
        }
    )
    summary.pop("status", None)
    summary.pop("ready_for_reviewer", None)
    summary.pop("ready_for_reviewer_scope", None)
    summary.pop("ready_for_reviewer_is_release_ready", None)
    return summary


def _write_v1384_reports(root: Path, overrides: dict[str, dict] | None = None) -> dict[str, dict]:
    overrides = overrides or {}
    summary = _base_summary_v1384()
    summary.update(overrides.get("summary", {}))
    recommendation = generate_v1_38_4_recommendation(summary)
    baseline_interp = build_v1_38_1_baseline_interpretation(summary)
    reports = {
        "ev_net_canonical_input_guard": {
            "canonical_base_version": "V1.37.2",
            "guard_status": "EV_NET_CANONICAL_INPUT_GUARD_PASSED",
            "real_data_enforced": True,
            "mock_data_detected": False,
            "raw_prediction_rows": 171648,
            "raw_prediction_rows_2026": 24360,
            "selection_dataset_rows": 171648,
            "selection_dataset_rows_2026": 24360,
            "outcome_dataset_rows": 171648,
            "outcome_dataset_rows_2026": 24360,
            "opportunity_index_rows": 171648,
            "opportunity_index_rows_2026": 24360,
        },
        "ev_net_feature_rebuild": {
            "selection_outcome_split_status": "PREDICTION_FRAME_INTEGRITY_PASSED",
            "selection_frame_forbidden_columns": [],
            "default_payoff_used": False,
            "fallback_probability_used": False,
            "artificial_probability_threshold_used": False,
            "ev_feature_rebuild_status": "EV_NET_FEATURE_REBUILD_COMPLETE",
        },
        "ev_net_filter_grid": {
            "filters_tested": [
                {"filter_name": "filter_ev_gt_cost_buffer", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_gt_0", "causal_status": "CAUSAL"},
                {"filter_name": "filter_prob_65_ev_pos", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_top_quantile_causal", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_top_quantile_non_causal", "causal_status": "RETROSPECTIVE_ONLY_FULL_PERIOD_QUANTILE"},
            ],
            "eligible_filters": [
                "filter_ev_gt_cost_buffer",
                "filter_ev_gt_0",
                "filter_prob_65_ev_pos",
                "filter_ev_top_quantile_causal",
            ],
            "excluded_filters": ["filter_ev_top_quantile_non_causal"],
            "exclusion_reasons": {"filter_ev_top_quantile_non_causal": "full_period_quantile_non_causal"},
            "causal_filter_count": 4,
            "non_causal_filter_count": 1,
            "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED",
        },
        "ev_net_filter_evaluation": {
            "status": "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED",
            "results": [
                {"filter_name": "filter_ev_gt_0", "selected_count": 129527},
            ],
        },
        "ev_net_random_baselines": {
            "status": "EV_NET_CANONICAL_RANDOM_BASELINES_COMPLETED",
            "results": [
                {"filter_name": "filter_ev_gt_0", "baseline_type": "GLOBAL_SAME_COUNT", "beats_random_p95": False},
                {"filter_name": "filter_ev_gt_0", "baseline_type": "MONTHLY_COUNT_PRESERVING", "beats_random_p95": True},
            ],
        },
        "ev_net_temporal_robustness": {
            "status": "EV_NET_CANONICAL_TEMPORAL_ROBUSTNESS_COMPLETED",
            "temporal_results": [],
            "summary_by_filter": {
                "filter_ev_gt_0": {
                    "active_windows_count": 4,
                    "recent_2026_selected_count": 19497,
                    "recent_2026_pnl": -0.00321872050730674,
                    "activity_status": "RECENT_WINDOW_NEGATIVE",
                }
            },
        },
        "ev_net_regime_robustness": {
            "status": "REGIME_ANALYSIS_COMPLETED",
            "results": [],
        },
        "ev_net_overfit_guard": {
            "evidence_classification": "EXPLORATORY_ONLY",
            "preregistration_allowed": False,
            "paper_live_allowed": False,
        },
        "ev_net_baseline_interpretation": baseline_interp,
        "ev_net_reviewer_readiness_semantics": {
            "release_ready_for_external_review": True,
            "strategy_reviewer_ready": False,
            "strategy_reviewer_ready_reason": "recent 2026 window negative and no strategy validated",
            "paper_live_ready": False,
            "preregistration_ready": False,
            "money_deployment_ready": False,
            "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
        },
        "ev_net_research_summary": summary,
        "ev_net_research_consistency_check": {
            "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
            "issues": [],
            "version": "V1.38.4",
            "status_field_policy": "REMOVED",
            "project_state_structured": True,
            "project_state_paths_aligned": True,
            "latest_metrics_aligned": True,
            "release_ready_inconsistency_fixed": True,
            "baseline_reporting_clarified": True,
            "legacy_status_field_removed_or_mirrored": True,
            "reviewer_readiness_semantics_clarified": True,
            "ambiguous_ready_for_reviewer_removed": True,
            "status_field_present": False,
            "status_field_matches_consistency_check_status": True,
        },
        "recommendation": recommendation,
    }
    reports["ev_net_research_consistency_check"].pop("status", None)

    for key, payload in overrides.items():
        if key in reports:
            reports[key].update(payload)
        elif key == "summary":
            reports["ev_net_research_summary"].update(payload)

    report_dir = root / "reports" / "research"
    for name, payload in reports.items():
        filename = f"{name}_v1_38_4.json" if name != "recommendation" else "v1_38_4_recommendation.json"
        _write_json(report_dir / filename, payload)
        md_name = filename.replace(".json", ".md")
        (report_dir / md_name).write_text("# test\n", encoding="utf-8")

    release_payload = {
        "version": "V1.38.4",
        "final_zip_created": True,
        "final_zip_path": "projet-galapagos-v1.38.4-clean.zip",
        "final_zip_contains_audit_reports": True,
        "final_zip_contains_smoke_reports": True,
        "final_audit_passed": True,
        "final_smoke_passed": True,
        "final_consistency_passed": True,
        "final_missing_required_files": [],
        "final_forbidden_count": 0,
        "final_secret_hits": [],
        "release_ready_for_external_review": True,
        "consistency_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
    }
    _write_json(root / "reports" / "release_zip_v1_38_4.json", release_payload)
    (root / "reports" / "release_zip_v1_38_4.md").write_text("# release\n", encoding="utf-8")

    _write_json(root / "reports" / "PROJECT_STATE.json", {
        "version": "V1.38.4",
        "previous_base": "V1.38.3",
        "purpose": "EV-net consistency check status field self-consistency fix",
        "final_verdict": summary["final_verdict"],
        "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
        "evidence_classification": "EXPLORATORY_ONLY",
        "recommended_next_step": summary["recommended_next_step"],
        "release_ready_for_external_review": True,
        "strategy_reviewer_ready": False,
        "paper_live_ready": False,
        "preregistration_ready": False,
        "money_deployment_ready": False,
        "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "canonical_base_version": "V1.37.2",
        "project_state_structured": True,
        "baseline_reporting_status": "EV_NET_BASELINE_REPORTING_CLARIFIED",
        "recommendation_artifact_json_path": "reports/research/v1_38_4_recommendation.json",
        "recommendation_artifact_md_path": "reports/research/v1_38_4_recommendation.md",
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "ambiguous_ready_for_reviewer_removed": True,
        "canonical_universe_context": {
            "canonical_base_version": "V1.37.2",
            "canonical_opportunity_rows": 171648,
            "canonical_opportunity_rows_2026": 24360,
            "selection_dataset_rows": 171648,
            "outcome_dataset_rows": 171648,
            "opportunity_index_rows": 171648,
            "ev_feature_status": "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
            "cost_policy_status": "COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
            "no_filter_applied_to_canonical_opportunity_universe": True,
        },
        "v1_38_research_context": {
            "ev_feature_rebuild_status": "EV_NET_FEATURE_REBUILD_COMPLETE",
            "ev_ready_rows": 134436,
            "ev_ready_rows_2026": 24360,
            "rows_blocked_by_warmup_count": 37212,
            "default_payoff_used": False,
            "fallback_probability_used": False,
            "artificial_probability_threshold_used": False,
            "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED",
            "evaluation_status": "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED",
            "best_filter_observed": "filter_ev_gt_0",
            "best_filter_mean_net_pnl": -2.6852081489793344e-05,
            "best_filter_2026_mean_net_pnl": -0.00321872050730674,
        },
    },)
    (root / "reports" / "PROJECT_STATE.md").write_text("# state\n", encoding="utf-8")
    metrics = summary.copy()
    metrics.pop("ready_for_reviewer", None)
    metrics.pop("ready_for_reviewer_scope", None)
    metrics.pop("ready_for_reviewer_is_release_ready", None)
    _write_json(root / "reports" / "current" / "latest_metrics.json", metrics)
    (root / "reports" / "current" / "latest_summary.md").write_text("# summary\n", encoding="utf-8")

    return reports


def _write_v138_reports(root: Path, overrides: dict[str, dict] | None = None) -> dict[str, dict]:
    overrides = overrides or {}
    summary = _base_summary()
    summary.update(overrides.get("summary", {}))
    recommendation = generate_v1_38_recommendation(summary)
    reports = {
        "ev_net_canonical_input_guard": {
            "canonical_base_version": "V1.37.2",
            "guard_status": "EV_NET_CANONICAL_INPUT_GUARD_PASSED",
            "real_data_enforced": True,
            "mock_data_detected": False,
            "raw_prediction_rows": 171648,
            "raw_prediction_rows_2026": 24360,
            "selection_dataset_rows": 171648,
            "selection_dataset_rows_2026": 24360,
            "outcome_dataset_rows": 171648,
            "outcome_dataset_rows_2026": 24360,
            "opportunity_index_rows": 171648,
            "opportunity_index_rows_2026": 24360,
        },
        "ev_net_feature_rebuild": {
            "selection_outcome_split_status": "PREDICTION_FRAME_INTEGRITY_PASSED",
            "selection_frame_forbidden_columns": [],
            "default_payoff_used": False,
            "fallback_probability_used": False,
            "artificial_probability_threshold_used": False,
            "ev_feature_rebuild_status": "EV_NET_FEATURE_REBUILD_COMPLETE",
        },
        "ev_net_filter_grid": {
            "filters_tested": [
                {"filter_name": "filter_ev_gt_cost_buffer", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_gt_0", "causal_status": "CAUSAL"},
                {"filter_name": "filter_prob_65_ev_pos", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_top_quantile_causal", "causal_status": "CAUSAL"},
                {"filter_name": "filter_ev_top_quantile_non_causal", "causal_status": "RETROSPECTIVE_ONLY_FULL_PERIOD_QUANTILE"},
            ],
            "eligible_filters": [
                "filter_ev_gt_cost_buffer",
                "filter_ev_gt_0",
                "filter_prob_65_ev_pos",
                "filter_ev_top_quantile_causal",
            ],
            "excluded_filters": ["filter_ev_top_quantile_non_causal"],
            "exclusion_reasons": {"filter_ev_top_quantile_non_causal": "full_period_quantile_non_causal"},
            "causal_filter_count": 4,
            "non_causal_filter_count": 1,
            "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED",
        },
        "ev_net_filter_evaluation": {
            "status": "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED",
            "results": [
                {"filter_name": "filter_ev_gt_cost_buffer", "selected_count": 122},
            ],
        },
        "ev_net_random_baselines": {
            "status": "EV_NET_CANONICAL_RANDOM_BASELINES_COMPLETED",
            "results": [
                {
                    "filter_name": "filter_ev_gt_cost_buffer",
                    "baseline_type": "MONTHLY_COUNT_PRESERVING",
                    "beats_random_p95": True,
                }
            ],
        },
        "ev_net_temporal_robustness": {
            "status": "EV_NET_CANONICAL_TEMPORAL_ROBUSTNESS_COMPLETED",
            "temporal_results": [],
            "summary_by_filter": {
                "filter_ev_gt_cost_buffer": {
                    "active_windows_count": 4,
                    "recent_2026_selected_count": 24,
                    "recent_2026_pnl": 0.004,
                    "activity_status": "TEMPORALLY_ACTIVE",
                }
            },
        },
        "ev_net_regime_robustness": {
            "status": "REGIME_ANALYSIS_COMPLETED",
            "results": [],
        },
        "ev_net_overfit_guard": {
            "evidence_classification": "EXPLORATORY_ONLY",
            "preregistration_allowed": False,
            "paper_live_allowed": False,
        },
        "ev_net_research_summary": summary,
        "ev_net_research_consistency_check": {
            "status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
            "issues": [],
            "version": "V1.38",
        },
        "recommendation": recommendation,
    }

    for key, payload in overrides.items():
        if key in reports:
            reports[key].update(payload)
        elif key == "summary":
            reports["ev_net_research_summary"].update(payload)

    report_dir = root / "reports" / "research"
    for name, payload in reports.items():
        _write_json(report_dir / f"{name}_v1_38.json" if name != "recommendation" else report_dir / "v1_38_recommendation.json", payload)
        md_name = f"{name}_v1_38.md" if name != "recommendation" else "v1_38_recommendation.md"
        (report_dir / md_name).write_text("# test\n", encoding="utf-8")

    _write_json(root / "reports" / "PROJECT_STATE.json", summary)
    _write_json(root / "reports" / "current" / "latest_metrics.json", summary)
    (root / "reports" / "PROJECT_STATE.md").write_text("# state\n", encoding="utf-8")
    (root / "reports" / "current" / "latest_summary.md").write_text("# summary\n", encoding="utf-8")

    return reports


def test_canonical_input_guard_flags_mock_path(tmp_path: Path) -> None:
    guard = audit_canonical_input_guard(
        canonical_summary_path=tmp_path / "canonical_summary.json",
        canonical_consistency_path=tmp_path / "canonical_consistency.json",
        predictions_path="data/mock_predictions.parquet",
        dataset_path="data/gold/research_dataset/BTC/4h/real.parquet",
        intrabar_path="data/silver/intrabar/binance/BTCUSDT/5m/real.parquet",
    )
    assert guard["mock_data_detected"] is True
    assert guard["guard_status"] == "EV_NET_CANONICAL_INPUT_GUARD_FAILED"


def test_canonical_ev_feature_rebuild_sets_causal_aliases() -> None:
    dates = pd.date_range("2024-01-01", periods=3000, freq="4h")
    df = pd.DataFrame(
        {
            "timestamp": dates,
            "predicted_probability": np.linspace(0.2, 0.8, len(dates)),
            "actual_target": [1, 0] * (len(dates) // 2) + [1] * (len(dates) % 2),
            "forward_return_12bar": np.where(np.arange(len(dates)) % 2 == 0, 0.05, -0.02),
        }
    )
    rebuilt, report = rebuild_canonical_ev_features(df)
    assert "predicted_probability_calibrated" in rebuilt.columns
    assert report["fallback_probability_used"] is False
    assert report["default_payoff_used"] is False
    assert report["artificial_probability_threshold_used"] is False
    assert report["selection_outcome_split_status"] == "PREDICTION_FRAME_INTEGRITY_PASSED"


def test_validator_v138_accepts_consistent_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v138_reports(tmp_path)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    assert res["issues"] == []


def test_validator_v138_rejects_wrong_base_and_counts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v138_reports(
        tmp_path,
        overrides={
            "guard": {
                "canonical_base_version": "V1.36.8",
                "raw_prediction_rows": 10,
            },
        },
    )
    report_dir = tmp_path / "reports" / "research"
    guard_path = report_dir / "ev_net_canonical_input_guard_v1_38.json"
    guard = json.loads(guard_path.read_text(encoding="utf-8"))
    guard["canonical_base_version"] = "V1.36.8"
    guard["raw_prediction_rows"] = 10
    _write_json(guard_path, guard)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38", report_dir=str(report_dir))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("canonical_base_version" in issue for issue in res["issues"])
    assert any("raw_prediction_rows must be 171648" in issue for issue in res["issues"])


def test_validator_v138_rejects_leaks_and_fallbacks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v138_reports(
        tmp_path,
        overrides={
            "rebuild": {
                "default_payoff_used": True,
                "fallback_probability_used": True,
            }
        },
    )
    report_dir = tmp_path / "reports" / "research"
    rebuild_path = report_dir / "ev_net_feature_rebuild_v1_38.json"
    rebuild = json.loads(rebuild_path.read_text(encoding="utf-8"))
    rebuild["selection_frame_forbidden_columns"] = ["forward_return_12bar"]
    rebuild["default_payoff_used"] = True
    rebuild["fallback_probability_used"] = True
    _write_json(rebuild_path, rebuild)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38", report_dir=str(report_dir))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("Forbidden outcome columns leaked" in issue for issue in res["issues"])
    assert any("default_payoff_used must be false" in issue for issue in res["issues"])
    assert any("fallback_probability_used must be false" in issue for issue in res["issues"])


def test_validator_v138_enforces_exploratory_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v138_reports(
        tmp_path,
        overrides={
            "summary": {
                "evidence_classification": "VALIDATED",
            }
        },
    )
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("evidence_classification" in issue for issue in res["issues"])


def test_v138_recommendation_is_exploratory_only() -> None:
    recs = generate_v1_38_recommendation(
        {
            "best_filter_observed": "filter_ev_gt_cost_buffer",
            "best_filter_selected_count_2026": 24,
            "best_filter_2026_mean_net_pnl": 0.004,
            "beats_monthly_random_p95": True,
            "active_windows_count": 4,
            "recent_window_status": "TEMPORALLY_ACTIVE",
        }
    )
    assert recs["evidence_classification"] == "EXPLORATORY_ONLY"
    assert recs["no_strategy_validated"] is True
    assert recs["no_real_trading"] is True


def test_validator_v1381_accepts_consistent_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1381_reports(tmp_path)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.1", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    assert res["issues"] == []


def test_release_ready_true_if_all_checks_pass(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1381_reports(tmp_path)
    release = json.loads((tmp_path / "reports" / "release_zip_v1_38_1.json").read_text(encoding="utf-8"))
    assert release["release_ready_for_external_review"] is True
    assert release["final_audit_passed"] is True
    assert release["final_smoke_passed"] is True
    assert release["final_consistency_passed"] is True


def test_validator_v1381_rejects_stale_recommendation_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1381_reports(tmp_path)
    state_path = tmp_path / "reports" / "PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["recommendation_artifact_json_path"] = "reports/research/v1_37_1_recommendation.json"
    state["recommendation_artifact_md_path"] = "reports/research/v1_37_1_recommendation.md"
    _write_json(state_path, state)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.1", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("recommendation_artifact_json_path" in issue for issue in res["issues"])


def test_validator_v1381_rejects_missing_baseline_reporting_fields(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1381_reports(tmp_path)
    summary_path = tmp_path / "reports" / "research" / "ev_net_research_summary_v1_38_1.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.pop("beats_global_random_p95", None)
    _write_json(summary_path, summary)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.1", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("beats_global_random_p95" in issue for issue in res["issues"])


def test_validator_v1382_accepts_consistent_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1382_reports(tmp_path)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.2", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    assert res["issues"] == []


def test_validator_v1382_rejects_ambiguous_ready_for_reviewer(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1382_reports(tmp_path)
    summary_path = tmp_path / "reports" / "research" / "ev_net_research_summary_v1_38_2.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["ready_for_reviewer"] = False
    summary.pop("ready_for_reviewer_scope", None)
    summary.pop("ready_for_reviewer_is_release_ready", None)
    _write_json(summary_path, summary)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.2", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("ready_for_reviewer" in issue for issue in res["issues"])


def test_validator_v1382_rejects_strategy_reviewer_ready_true(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1382_reports(tmp_path)
    summary_path = tmp_path / "reports" / "research" / "ev_net_research_summary_v1_38_2.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["strategy_reviewer_ready"] = True
    _write_json(summary_path, summary)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.2", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("strategy_reviewer_ready" in issue for issue in res["issues"])


def test_validator_v1382_rejects_changed_best_filter_metrics(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1382_reports(tmp_path)
    summary_path = tmp_path / "reports" / "research" / "ev_net_research_summary_v1_38_2.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["best_filter_mean_net_pnl"] = 0.0
    _write_json(summary_path, summary)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.2", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("best_filter_mean_net_pnl" in issue for issue in res["issues"])


def test_validator_v1383_accepts_consistent_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1383_reports(tmp_path)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.3", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    assert res["issues"] == []


def test_validator_v1383_rejects_ready_for_reviewer_in_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1383_reports(tmp_path)
    state_path = tmp_path / "reports" / "PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["ready_for_reviewer"] = False
    _write_json(state_path, state)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.3", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("ready_for_reviewer" in issue for issue in res["issues"])


def test_validator_v1383_rejects_ready_for_reviewer_in_latest_metrics(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1383_reports(tmp_path)
    metrics_path = tmp_path / "reports" / "current" / "latest_metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics["ready_for_reviewer"] = False
    _write_json(metrics_path, metrics)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.3", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("ready_for_reviewer" in issue for issue in res["issues"])


def test_validator_v1383_rejects_changed_best_filter_metrics(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1383_reports(tmp_path)
    summary_path = tmp_path / "reports" / "research" / "ev_net_research_summary_v1_38_3.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["best_filter_mean_net_pnl"] = 0.0
    _write_json(summary_path, summary)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.3", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("best_filter_mean_net_pnl" in issue for issue in res["issues"])


def test_validator_v1384_accepts_consistency_status_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1384_reports(tmp_path)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.4", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    assert res["issues"] == []


def test_validator_v1384_rejects_legacy_status_in_consistency_check(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1384_reports(tmp_path)
    report_dir = tmp_path / "reports" / "research"
    consistency_path = report_dir / "ev_net_research_consistency_check_v1_38_4.json"
    consistency = json.loads(consistency_path.read_text(encoding="utf-8"))
    consistency["status"] = consistency["consistency_check_status"]
    _write_json(consistency_path, consistency)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.4", report_dir=str(report_dir))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("legacy status" in issue.lower() for issue in res["issues"])


def test_validator_v1384_rejects_status_field_present_true(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1384_reports(tmp_path)
    report_dir = tmp_path / "reports" / "research"
    consistency_path = report_dir / "ev_net_research_consistency_check_v1_38_4.json"
    consistency = json.loads(consistency_path.read_text(encoding="utf-8"))
    consistency["status_field_present"] = True
    _write_json(consistency_path, consistency)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.4", report_dir=str(report_dir))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("status_field_present" in issue for issue in res["issues"])


def test_validator_v1384_rejects_ready_for_reviewer_in_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_v1384_reports(tmp_path)
    state_path = tmp_path / "reports" / "PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["ready_for_reviewer"] = False
    _write_json(state_path, state)
    validate_reports = _load_validate_reports()
    res = validate_reports("v1.38.4", report_dir=str(tmp_path / "reports" / "research"))
    assert res["status"] == "EV_NET_CANONICAL_RESEARCH_REPORTS_INCONSISTENT"
    assert any("ready_for_reviewer" in issue for issue in res["issues"])
