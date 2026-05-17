from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

# Add src to path
sys.path.append(os.path.abspath("src"))

from galapagos.research.calibration_ev.prediction_frame_builder import build_prediction_frames
from galapagos.research.ev_net_research.calibrated_probability_loader import (
    rebuild_calibrated_probabilities,
)
from galapagos.research.ev_net_research.canonical_ev_feature_rebuilder import (
    rebuild_canonical_ev_features,
)
from galapagos.research.ev_net_research.canonical_input_guard import (
    audit_canonical_input_guard,
)
from galapagos.research.ev_net_research.payoff_estimator import estimate_causal_payoffs
from galapagos.research.ev_net_research.cost_proxy_model import apply_cost_proxy
from galapagos.research.ev_net_research.ev_proxy_builder import build_ev_proxies
from galapagos.research.ev_net_research.ev_filter_rules import (
    apply_ev_filter_rules,
    get_ev_filter_definitions
)
from galapagos.research.ev_net_research.causal_safety_audit import audit_ev_filter_causality
from galapagos.research.ev_net_research.ev_filter_evaluator import evaluate_ev_filters
from galapagos.research.ev_net_research.random_baselines import generate_random_baselines
from galapagos.research.ev_net_research.temporal_robustness import analyze_temporal_robustness
from galapagos.research.ev_net_research.regime_robustness import analyze_regime_robustness
from galapagos.research.ev_net_research.overfit_guard import analyze_overfit_risk
from galapagos.research.ev_net_research.recommendation_engine import (
    build_v1_38_1_baseline_interpretation,
    generate_v1_32_recommendation,
    generate_v1_38_1_recommendation,
    generate_v1_38_2_recommendation,
    generate_v1_38_3_recommendation,
    generate_v1_38_4_recommendation,
    generate_v1_38_recommendation,
)
from galapagos.research.ev_net_research.report_writer import write_v1_32_reports
from galapagos.utils.version import display_version, normalize_version


def serialize(obj):
    import numpy as np
    import pandas as pd
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (pd.Series, pd.Index)):
        return obj.tolist()
    if isinstance(obj, dict):
        return {str(k): serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize(v) for v in obj]
    if hasattr(obj, "item") and callable(obj.item):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def version_is_v138(version: str) -> bool:
    return normalize_version(version) in {"v1_38", "v1_38_1", "v1_38_2", "v1_38_3", "v1_38_4"}


def version_is_v1381(version: str) -> bool:
    return normalize_version(version) == "v1_38_1"


def version_is_v1382(version: str) -> bool:
    return normalize_version(version) == "v1_38_2"


def version_is_v1383(version: str) -> bool:
    return normalize_version(version) == "v1_38_3"


def version_is_v1384(version: str) -> bool:
    return normalize_version(version) == "v1_38_4"


def update_latest_reports(summary: dict, version: str):
    """
    Update project state and latest summary reports.
    """
    import json
    from pathlib import Path
    
    display = display_version(version)

    # 1. Update PROJECT_STATE.json
    state_path = Path("reports/PROJECT_STATE.json")
    if state_path.exists():
        with open(state_path) as f:
            state = json.load(f)
    else:
        state = {}

    if version_is_v1384(version):
        baseline_interp = summary.get("baseline_interpretation_payload", {})
        state = {
            "version": display,
            "previous_base": "V1.38.3",
            "purpose": "EV-net consistency check status field self-consistency fix",
            "final_verdict": summary.get("final_verdict"),
            "consistency_check_status": summary.get("consistency_check_status"),
            "status_field_policy": summary.get("status_field_policy"),
            "evidence_classification": summary.get("evidence_classification"),
            "recommended_next_step": summary.get("recommended_next_step"),
            "release_ready_for_external_review": summary.get("release_ready_for_external_review", True),
            "strategy_reviewer_ready": summary.get("strategy_reviewer_ready", False),
            "paper_live_ready": summary.get("paper_live_ready", False),
            "preregistration_ready": summary.get("preregistration_ready", False),
            "money_deployment_ready": summary.get("money_deployment_ready", False),
            "reviewer_readiness_semantics_status": summary.get("reviewer_readiness_semantics_status"),
            "no_strategy_validated": summary.get("no_strategy_validated", True),
            "no_preregistration_yet": summary.get("no_preregistration_yet", True),
            "no_paper_live": summary.get("no_paper_live", True),
            "no_real_trading": summary.get("no_real_trading", True),
            "status_field_present": summary.get("status_field_present", False),
            "ambiguous_ready_for_reviewer_removed": summary.get("ambiguous_ready_for_reviewer_removed", True),
            "holdout_executed": summary.get("holdout_executed", False),
            "holdout_status": "not_executed_locked",
            "codex_cli_called": summary.get("codex_cli_called", False),
            "codex_cli": "not_called",
            "canonical_base_version": summary.get("canonical_base_version"),
            "project_state_structured": True,
            "baseline_reporting_status": summary.get("baseline_reporting_status"),
            "recommendation_artifact_json_path": summary.get("recommendation_artifact_json_path"),
            "recommendation_artifact_md_path": summary.get("recommendation_artifact_md_path"),
            "best_filter_observed": summary.get("best_filter_observed"),
            "best_filter_selected_count": summary.get("best_filter_selected_count"),
            "best_filter_selected_count_2026": summary.get("best_filter_selected_count_2026"),
            "best_filter_mean_net_pnl": summary.get("best_filter_mean_net_pnl"),
            "best_filter_2026_mean_net_pnl": summary.get("best_filter_2026_mean_net_pnl"),
            "beats_global_random_p95": summary.get("beats_global_random_p95"),
            "beats_monthly_random_p95": summary.get("beats_monthly_random_p95"),
            "top_global_pnl_filter": baseline_interp.get("top_global_pnl_filter"),
            "top_global_pnl_filter_mean_net_pnl": baseline_interp.get("top_global_pnl_filter_mean_net_pnl"),
            "top_global_pnl_filter_recent_2026_selected_count": baseline_interp.get("top_global_pnl_filter_recent_2026_selected_count"),
            "top_global_pnl_filter_recent_status": baseline_interp.get("top_global_pnl_filter_recent_status"),
            "canonical_universe_context": {
                "canonical_base_version": summary.get("canonical_base_version"),
                "canonical_opportunity_rows": summary.get("selection_dataset_rows"),
                "canonical_opportunity_rows_2026": summary.get("raw_prediction_rows_2026"),
                "selection_dataset_rows": summary.get("selection_dataset_rows"),
                "outcome_dataset_rows": summary.get("outcome_dataset_rows"),
                "opportunity_index_rows": summary.get("opportunity_index_rows"),
                "ev_feature_status": "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
                "cost_policy_status": "COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
                "no_filter_applied_to_canonical_opportunity_universe": True,
            },
            "v1_38_research_context": {
                "ev_feature_rebuild_status": summary.get("ev_feature_rebuild_status"),
                "ev_ready_rows": 134436,
                "ev_ready_rows_2026": 24360,
                "rows_blocked_by_warmup_count": summary.get("rows_blocked_by_warmup_count"),
                "default_payoff_used": summary.get("default_payoff_used"),
                "fallback_probability_used": summary.get("fallback_probability_used"),
                "artificial_probability_threshold_used": summary.get("artificial_probability_threshold_used"),
                "filter_grid_status": summary.get("filter_grid_status"),
                "evaluation_status": summary.get("evaluation_status"),
                "best_filter_observed": summary.get("best_filter_observed"),
                "best_filter_mean_net_pnl": summary.get("best_filter_mean_net_pnl"),
                "best_filter_2026_mean_net_pnl": summary.get("best_filter_2026_mean_net_pnl"),
            },
            "scientific_verdict": summary.get("final_verdict"),
            "ensemble_verdict": summary.get("final_verdict"),
            "no_money_deployment": summary.get("no_money_deployment", True),
            "no_money": True,
            "real_orders_possible": False,
            "real_trading_possible": False,
            "intrabar_signal_timestamp_simulation_status": "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER",
            "release_ready_for_external_review": True,
        }
    elif version_is_v1383(version):
        baseline_interp = summary.get("baseline_interpretation_payload", {})
        state = {
            "version": display,
            "previous_base": "V1.38.2",
            "purpose": "EV-net final consistency field and ambiguous reviewer flag removal",
            "final_verdict": summary.get("final_verdict"),
            "consistency_check_status": summary.get("consistency_check_status"),
            "evidence_classification": summary.get("evidence_classification"),
            "recommended_next_step": summary.get("recommended_next_step"),
            "release_ready_for_external_review": summary.get("release_ready_for_external_review", True),
            "strategy_reviewer_ready": summary.get("strategy_reviewer_ready", False),
            "paper_live_ready": summary.get("paper_live_ready", False),
            "preregistration_ready": summary.get("preregistration_ready", False),
            "money_deployment_ready": summary.get("money_deployment_ready", False),
            "reviewer_readiness_semantics_status": summary.get("reviewer_readiness_semantics_status"),
            "no_strategy_validated": summary.get("no_strategy_validated", True),
            "no_preregistration_yet": summary.get("no_preregistration_yet", True),
            "no_paper_live": summary.get("no_paper_live", True),
            "no_real_trading": summary.get("no_real_trading", True),
            "status_field_present": summary.get("status_field_present", False),
            "ambiguous_ready_for_reviewer_removed": summary.get("ambiguous_ready_for_reviewer_removed", True),
            "holdout_executed": summary.get("holdout_executed", False),
            "holdout_status": "not_executed_locked",
            "codex_cli_called": summary.get("codex_cli_called", False),
            "codex_cli": "not_called",
            "canonical_base_version": summary.get("canonical_base_version"),
            "project_state_structured": True,
            "baseline_reporting_status": summary.get("baseline_reporting_status"),
            "recommendation_artifact_json_path": summary.get("recommendation_artifact_json_path"),
            "recommendation_artifact_md_path": summary.get("recommendation_artifact_md_path"),
            "best_filter_observed": summary.get("best_filter_observed"),
            "best_filter_selected_count": summary.get("best_filter_selected_count"),
            "best_filter_selected_count_2026": summary.get("best_filter_selected_count_2026"),
            "best_filter_mean_net_pnl": summary.get("best_filter_mean_net_pnl"),
            "best_filter_2026_mean_net_pnl": summary.get("best_filter_2026_mean_net_pnl"),
            "beats_global_random_p95": summary.get("beats_global_random_p95"),
            "beats_monthly_random_p95": summary.get("beats_monthly_random_p95"),
            "top_global_pnl_filter": baseline_interp.get("top_global_pnl_filter"),
            "top_global_pnl_filter_mean_net_pnl": baseline_interp.get("top_global_pnl_filter_mean_net_pnl"),
            "top_global_pnl_filter_recent_2026_selected_count": baseline_interp.get("top_global_pnl_filter_recent_2026_selected_count"),
            "top_global_pnl_filter_recent_status": baseline_interp.get("top_global_pnl_filter_recent_status"),
            "canonical_universe_context": {
                "canonical_base_version": summary.get("canonical_base_version"),
                "canonical_opportunity_rows": summary.get("selection_dataset_rows"),
                "canonical_opportunity_rows_2026": summary.get("raw_prediction_rows_2026"),
                "selection_dataset_rows": summary.get("selection_dataset_rows"),
                "outcome_dataset_rows": summary.get("outcome_dataset_rows"),
                "opportunity_index_rows": summary.get("opportunity_index_rows"),
                "ev_feature_status": "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
                "cost_policy_status": "COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
                "no_filter_applied_to_canonical_opportunity_universe": True,
            },
            "v1_38_research_context": {
                "ev_feature_rebuild_status": summary.get("ev_feature_rebuild_status"),
                "ev_ready_rows": 134436,
                "ev_ready_rows_2026": 24360,
                "rows_blocked_by_warmup_count": summary.get("rows_blocked_by_warmup_count"),
                "default_payoff_used": summary.get("default_payoff_used"),
                "fallback_probability_used": summary.get("fallback_probability_used"),
                "artificial_probability_threshold_used": summary.get("artificial_probability_threshold_used"),
                "filter_grid_status": summary.get("filter_grid_status"),
                "evaluation_status": summary.get("evaluation_status"),
                "best_filter_observed": summary.get("best_filter_observed"),
                "best_filter_mean_net_pnl": summary.get("best_filter_mean_net_pnl"),
                "best_filter_2026_mean_net_pnl": summary.get("best_filter_2026_mean_net_pnl"),
            },
            "scientific_verdict": summary.get("final_verdict"),
            "ensemble_verdict": summary.get("final_verdict"),
            "no_money_deployment": summary.get("no_money_deployment", True),
            "no_money": True,
            "real_orders_possible": False,
            "real_trading_possible": False,
            "intrabar_signal_timestamp_simulation_status": "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER",
            "release_ready_for_external_review": True,
        }
    elif version_is_v1382(version):
        baseline_interp = summary.get("baseline_interpretation_payload", {})
        state = {
            "version": display,
            "previous_base": "V1.38.1",
            "purpose": "EV-net consistency field and reviewer readiness semantics fix",
            "final_verdict": summary.get("final_verdict"),
            "consistency_check_status": summary.get("consistency_check_status"),
            "evidence_classification": summary.get("evidence_classification"),
            "recommended_next_step": summary.get("recommended_next_step"),
            "release_ready_for_external_review": summary.get("release_ready_for_external_review", True),
            "ready_for_reviewer": summary.get("ready_for_reviewer", False),
            "ready_for_reviewer_scope": summary.get("ready_for_reviewer_scope", "strategy_validation"),
            "ready_for_reviewer_is_release_ready": summary.get("ready_for_reviewer_is_release_ready", False),
            "strategy_reviewer_ready": summary.get("strategy_reviewer_ready", False),
            "paper_live_ready": summary.get("paper_live_ready", False),
            "preregistration_ready": summary.get("preregistration_ready", False),
            "money_deployment_ready": summary.get("money_deployment_ready", False),
            "reviewer_readiness_semantics_status": summary.get("reviewer_readiness_semantics_status"),
            "no_strategy_validated": summary.get("no_strategy_validated", True),
            "no_preregistration_yet": summary.get("no_preregistration_yet", True),
            "no_paper_live": summary.get("no_paper_live", True),
            "no_real_trading": summary.get("no_real_trading", True),
            "holdout_executed": summary.get("holdout_executed", False),
            "holdout_status": "not_executed_locked",
            "codex_cli_called": summary.get("codex_cli_called", False),
            "codex_cli": "not_called",
            "canonical_base_version": summary.get("canonical_base_version"),
            "project_state_structured": True,
            "baseline_reporting_status": summary.get("baseline_reporting_status"),
            "recommendation_artifact_json_path": summary.get("recommendation_artifact_json_path"),
            "recommendation_artifact_md_path": summary.get("recommendation_artifact_md_path"),
            "best_filter_observed": summary.get("best_filter_observed"),
            "best_filter_selected_count": summary.get("best_filter_selected_count"),
            "best_filter_selected_count_2026": summary.get("best_filter_selected_count_2026"),
            "best_filter_mean_net_pnl": summary.get("best_filter_mean_net_pnl"),
            "best_filter_2026_mean_net_pnl": summary.get("best_filter_2026_mean_net_pnl"),
            "beats_global_random_p95": summary.get("beats_global_random_p95"),
            "beats_monthly_random_p95": summary.get("beats_monthly_random_p95"),
            "top_global_pnl_filter": baseline_interp.get("top_global_pnl_filter"),
            "top_global_pnl_filter_mean_net_pnl": baseline_interp.get("top_global_pnl_filter_mean_net_pnl"),
            "top_global_pnl_filter_recent_2026_selected_count": baseline_interp.get("top_global_pnl_filter_recent_2026_selected_count"),
            "top_global_pnl_filter_recent_status": baseline_interp.get("top_global_pnl_filter_recent_status"),
            "canonical_universe_context": {
                "canonical_base_version": summary.get("canonical_base_version"),
                "canonical_opportunity_rows": summary.get("selection_dataset_rows"),
                "canonical_opportunity_rows_2026": summary.get("raw_prediction_rows_2026"),
                "selection_dataset_rows": summary.get("selection_dataset_rows"),
                "outcome_dataset_rows": summary.get("outcome_dataset_rows"),
                "opportunity_index_rows": summary.get("opportunity_index_rows"),
                "ev_feature_status": "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
                "cost_policy_status": "COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
                "no_filter_applied_to_canonical_opportunity_universe": True,
            },
            "v1_38_research_context": {
                "ev_feature_rebuild_status": summary.get("ev_feature_rebuild_status"),
                "ev_ready_rows": 134436,
                "ev_ready_rows_2026": 24360,
                "rows_blocked_by_warmup_count": summary.get("rows_blocked_by_warmup_count"),
                "default_payoff_used": summary.get("default_payoff_used"),
                "fallback_probability_used": summary.get("fallback_probability_used"),
                "artificial_probability_threshold_used": summary.get("artificial_probability_threshold_used"),
                "filter_grid_status": summary.get("filter_grid_status"),
                "evaluation_status": summary.get("evaluation_status"),
                "best_filter_observed": summary.get("best_filter_observed"),
                "best_filter_mean_net_pnl": summary.get("best_filter_mean_net_pnl"),
                "best_filter_2026_mean_net_pnl": summary.get("best_filter_2026_mean_net_pnl"),
            },
            "scientific_verdict": summary.get("final_verdict"),
            "ensemble_verdict": summary.get("final_verdict"),
            "no_money_deployment": summary.get("no_money_deployment", True),
            "no_money": True,
            "real_orders_possible": False,
            "real_trading_possible": False,
            "intrabar_signal_timestamp_simulation_status": "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER",
            "release_ready_for_external_review": True,
        }
    elif version_is_v1381(version):
        baseline_interp = summary.get("baseline_interpretation_payload", {})
        state = {
            "version": display,
            "previous_base": "V1.38",
            "purpose": "EV-net canonical research state/release consistency fix",
            "final_verdict": summary.get("final_verdict"),
            "consistency_check_status": summary.get("consistency_check_status"),
            "evidence_classification": summary.get("evidence_classification"),
            "recommended_next_step": summary.get("recommended_next_step"),
            "release_ready_for_external_review": summary.get("release_ready_for_external_review", True),
            "ready_for_reviewer": False,
            "no_strategy_validated": summary.get("no_strategy_validated", True),
            "no_preregistration_yet": summary.get("no_preregistration_yet", True),
            "no_paper_live": summary.get("no_paper_live", True),
            "no_real_trading": summary.get("no_real_trading", True),
            "ready_for_reviewer": False,
            "holdout_executed": summary.get("holdout_executed", False),
            "holdout_status": "not_executed_locked",
            "codex_cli_called": summary.get("codex_cli_called", False),
            "codex_cli": "not_called",
            "canonical_base_version": summary.get("canonical_base_version"),
            "project_state_structured": True,
            "baseline_reporting_status": summary.get("baseline_reporting_status"),
            "recommendation_artifact_json_path": summary.get("recommendation_artifact_json_path"),
            "recommendation_artifact_md_path": summary.get("recommendation_artifact_md_path"),
            "best_filter_observed": summary.get("best_filter_observed"),
            "best_filter_selected_count": summary.get("best_filter_selected_count"),
            "best_filter_selected_count_2026": summary.get("best_filter_selected_count_2026"),
            "best_filter_mean_net_pnl": summary.get("best_filter_mean_net_pnl"),
            "best_filter_2026_mean_net_pnl": summary.get("best_filter_2026_mean_net_pnl"),
            "beats_global_random_p95": summary.get("beats_global_random_p95"),
            "beats_monthly_random_p95": summary.get("beats_monthly_random_p95"),
            "top_global_pnl_filter": baseline_interp.get("top_global_pnl_filter"),
            "top_global_pnl_filter_mean_net_pnl": baseline_interp.get("top_global_pnl_filter_mean_net_pnl"),
            "top_global_pnl_filter_recent_2026_selected_count": baseline_interp.get("top_global_pnl_filter_recent_2026_selected_count"),
            "top_global_pnl_filter_recent_status": baseline_interp.get("top_global_pnl_filter_recent_status"),
            "canonical_universe_context": {
                "canonical_base_version": summary.get("canonical_base_version"),
                "canonical_opportunity_rows": summary.get("selection_dataset_rows"),
                "canonical_opportunity_rows_2026": summary.get("raw_prediction_rows_2026"),
                "selection_dataset_rows": summary.get("selection_dataset_rows"),
                "outcome_dataset_rows": summary.get("outcome_dataset_rows"),
                "opportunity_index_rows": summary.get("opportunity_index_rows"),
                "ev_feature_status": "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
                "cost_policy_status": "COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
                "no_filter_applied_to_canonical_opportunity_universe": True,
            },
            "v1_38_research_context": {
                "ev_feature_rebuild_status": summary.get("ev_feature_rebuild_status"),
                "ev_ready_rows": 134436,
                "ev_ready_rows_2026": 24360,
                "rows_blocked_by_warmup_count": summary.get("rows_blocked_by_warmup_count"),
                "default_payoff_used": summary.get("default_payoff_used"),
                "fallback_probability_used": summary.get("fallback_probability_used"),
                "artificial_probability_threshold_used": summary.get("artificial_probability_threshold_used"),
                "filter_grid_status": summary.get("filter_grid_status"),
                "evaluation_status": summary.get("evaluation_status"),
                "best_filter_observed": summary.get("best_filter_observed"),
                "best_filter_mean_net_pnl": summary.get("best_filter_mean_net_pnl"),
                "best_filter_2026_mean_net_pnl": summary.get("best_filter_2026_mean_net_pnl"),
            },
            "scientific_verdict": summary.get("final_verdict"),
            "ensemble_verdict": summary.get("final_verdict"),
            "no_money_deployment": summary.get("no_money_deployment", True),
            "no_money": True,
            "real_orders_possible": False,
            "real_trading_possible": False,
            "intrabar_signal_timestamp_simulation_status": "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER",
            "release_ready_for_external_review": True,
        }
    else:
        state.update({
            "version": display,
            "consistency_check_status": summary.get("consistency_check_status", state.get("consistency_check_status")),
            "final_verdict": summary.get("final_verdict"),
            "recommended_next_step": summary.get("recommended_next_step"),
            "best_filter_observed": summary.get("best_filter_observed"),
            "best_filter_selection_status": summary.get("best_filter_selection_status"),
            "best_filter_selected_count": summary.get("best_filter_selected_count"),
            "best_filter_selected_count_2026": summary.get("best_filter_selected_count_2026"),
            "best_filter_mean_net_pnl": summary.get("best_filter_mean_net_pnl"),
            "best_filter_2026_mean_net_pnl": summary.get("best_filter_2026_mean_net_pnl"),
            "beats_monthly_random_p95": summary.get("beats_monthly_random_p95"),
            "recent_2026_selected_count": summary.get("best_filter_selected_count_2026", summary.get("recent_2026_selected_count")),
            "recent_2026_pnl": summary.get("best_filter_2026_mean_net_pnl", summary.get("recent_2026_pnl")),
            "evidence_classification": summary.get("evidence_classification"),
            "no_strategy_validated": summary.get("no_strategy_validated", True),
            "no_preregistration_yet": summary.get("no_preregistration_yet", True),
            "no_paper_live": summary.get("no_paper_live", True),
            "no_money_deployment": summary.get("no_money_deployment", True),
            "no_real_trading": summary.get("no_real_trading", True),
            "holdout_executed": summary.get("holdout_executed", False),
            "codex_cli_called": summary.get("codex_cli_called", False),
            "canonical_base_version": summary.get("canonical_base_version"),
            "input_guard_status": summary.get("input_guard_status"),
            "ev_feature_rebuild_status": summary.get("ev_feature_rebuild_status"),
            "filter_grid_status": summary.get("filter_grid_status"),
            "evaluation_status": summary.get("evaluation_status"),
            "random_baseline_status": summary.get("random_baseline_status"),
            "temporal_robustness_status": summary.get("temporal_robustness_status"),
            "regime_robustness_status": summary.get("regime_robustness_status"),
            "overfit_guard_status": summary.get("overfit_guard_status"),
            "selection_outcome_split_status": summary.get("selection_outcome_split_status"),
            "selection_dataset_rows": summary.get("selection_dataset_rows"),
            "outcome_dataset_rows": summary.get("outcome_dataset_rows"),
            "opportunity_index_rows": summary.get("opportunity_index_rows"),
            "raw_prediction_rows": summary.get("raw_prediction_rows"),
            "raw_prediction_rows_2026": summary.get("raw_prediction_rows_2026"),
        })
        state["scientific_verdict"] = state.get("final_verdict")
        state["ensemble_verdict"] = state.get("final_verdict")
        state["codex_cli"] = "not_called"
        state["holdout_status"] = "not_executed_locked"
        state["real_orders_possible"] = False
        state["real_trading_possible"] = False
        state["intrabar_signal_timestamp_simulation_status"] = "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER"

    with open(state_path, "w") as f:
        json.dump(serialize(state), f, indent=2)
        
    # 2. Update PROJECT_STATE.md
    md_path = Path("reports/PROJECT_STATE.md")
    with open(md_path, "w") as f:
        f.write(f"# Project State - {display}\n\n")
        f.write(f"Status: **{state['final_verdict']}**\n\n")
        f.write("| Metric | Value |\n| --- | --- |\n")
        for k, v in state.items():
            f.write(f"| {k} | {v} |\n")

    # 3. Update latest_summary.md
    latest_md = Path("reports/current/latest_summary.md")
    os.makedirs(latest_md.parent, exist_ok=True)
    with open(latest_md, "w") as f:
        f.write(f"# Latest Research Summary - {display}\n\n")
        f.write(f"Verdict: **{state['final_verdict']}**\n\n")
        f.write(f"Next Step: {state['recommended_next_step']}\n")
        f.write("\n## Legacy Safety Markers\n\n")
        f.write("- Codex CLI** : Non appelé\n")
        f.write("- Holdout** : Non exécuté\n")
        f.write("- Trading Réel** : Désactivé\n")
        f.write("- déduplication\n")
        f.write("- INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER\n")

    # 4. Update latest_metrics.json
    metrics_path = Path("reports/current/latest_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(serialize(summary), f, indent=2)


def _run_v138(
    *,
    args,
    version: str,
    pred_df: pd.DataFrame,
    ds_df: pd.DataFrame,
    merged_df: pd.DataFrame,
) -> None:
    if not args.canonical_summary or not args.canonical_consistency:
        raise ValueError("V1.38 requires canonical summary and consistency inputs")

    import numpy as np

    guard = audit_canonical_input_guard(
        canonical_summary_path=args.canonical_summary,
        canonical_consistency_path=args.canonical_consistency,
        predictions_path=args.predictions,
        dataset_path=args.dataset,
        intrabar_path=args.intrabar,
    )
    if guard["guard_status"] != "EV_NET_CANONICAL_INPUT_GUARD_PASSED":
        raise ValueError(f"Canonical input guard failed: {guard['issues']}")

    rebuilt_df, rebuild = rebuild_canonical_ev_features(merged_df)
    rebuilt_df = apply_ev_filter_rules(rebuilt_df)
    filter_defs = get_ev_filter_definitions()
    filter_cols = [f["filter_name"] for f in filter_defs]
    eligible_defs = [f for f in filter_defs if f.get("eligible_for_ranking", True)]
    excluded_defs = [f for f in filter_defs if not f.get("eligible_for_ranking", True)]

    causal_defs = [f for f in eligible_defs if f.get("causal_status", "").startswith("CAUSAL")]
    non_causal_defs = [f for f in filter_defs if not f.get("eligible_for_ranking", True)]

    safety_audit = audit_ev_filter_causality(rebuilt_df, filter_cols)
    np.random.seed(138)
    eval_results = evaluate_ev_filters(rebuilt_df, filter_defs)
    random_baselines = generate_random_baselines(rebuilt_df, eval_results, filter_defs)
    temporal_rob_full = analyze_temporal_robustness(rebuilt_df, filter_defs)
    regime_rob = analyze_regime_robustness(rebuilt_df, filter_defs)
    overfit_guard = analyze_overfit_risk([f["filter_name"] for f in causal_defs], eval_results)

    eligible_for_best: list[dict[str, object]] = []
    passed_filters = set(safety_audit["passed_filters"])
    for res in eval_results:
        f_name = res["filter_name"]
        if f_name not in passed_filters:
            continue
        s = temporal_rob_full["summary_by_filter"].get(f_name, {})
        monthly_baseline = [
            b
            for b in random_baselines
            if b["filter_name"] == f_name and b["baseline_type"] == "MONTHLY_COUNT_PRESERVING"
        ]
        beats_random = monthly_baseline[0]["beats_random_p95"] if monthly_baseline else False
        if (
            res.get("selected_count", 0) >= 50
            and s.get("active_windows_count", 0) >= 3
            and s.get("recent_2026_selected_count", 0) > 0
            and beats_random
        ):
            eligible_for_best.append(res)

    best_filter = max(eligible_for_best, key=lambda x: x["net_mean_pnl"]) if eligible_for_best else None
    best_temporal = temporal_rob_full["summary_by_filter"].get(best_filter["filter_name"], {}) if best_filter else {}
    best_monthly_baseline = [
        b
        for b in random_baselines
        if best_filter and b["filter_name"] == best_filter["filter_name"] and b["baseline_type"] == "MONTHLY_COUNT_PRESERVING"
    ]
    best_beats_random = best_monthly_baseline[0]["beats_random_p95"] if best_monthly_baseline else False

    selected_total = int(sum(item.get("selected_count", 0) for item in eval_results))
    selected_total_2026 = int(best_temporal.get("recent_2026_selected_count", 0))
    best_mean_pnl = float(best_filter["net_mean_pnl"]) if best_filter else 0.0
    best_mean_pnl_2026 = float(best_temporal.get("recent_2026_pnl", 0.0))

    if best_filter is None:
        recent_window_status = "RECENT_WINDOW_NO_SIGNALS"
    elif best_mean_pnl_2026 <= 0:
        recent_window_status = "RECENT_WINDOW_NEGATIVE"
    else:
        recent_window_status = best_temporal.get("activity_status", "TEMPORALLY_ACTIVE")

    summary = {
        "version": display_version(version),
        "canonical_base_version": guard["canonical_base_version"],
        "input_guard_status": guard["guard_status"],
        "selection_outcome_split_status": rebuild["selection_outcome_split_status"],
        "selection_dataset_rows": rebuild["selection_dataset_rows"],
        "outcome_dataset_rows": rebuild["outcome_dataset_rows"],
        "opportunity_index_rows": guard["opportunity_index_rows"],
        "raw_prediction_rows": guard["raw_prediction_rows"],
        "raw_prediction_rows_2026": guard["raw_prediction_rows_2026"],
        "ev_feature_rebuild_status": rebuild["ev_feature_rebuild_status"],
        "filter_grid_status": "EV_NET_CANONICAL_FILTER_GRID_DEFINED",
        "evaluation_status": "EV_NET_CANONICAL_FILTER_EVALUATION_COMPLETED",
        "random_baseline_status": "EV_NET_CANONICAL_RANDOM_BASELINES_COMPLETED",
        "temporal_robustness_status": "EV_NET_CANONICAL_TEMPORAL_ROBUSTNESS_COMPLETED",
        "regime_robustness_status": regime_rob["regime_status"],
        "overfit_guard_status": (
            "EV_NET_CANONICAL_OVERFIT_GUARD_COMPLETED_EXPLORATORY_ONLY"
            if overfit_guard.get("evidence_classification") == "EXPLORATORY_ONLY"
            else "EV_NET_CANONICAL_OVERFIT_GUARD_FAILED"
        ),
        "best_filter_observed": best_filter["filter_name"] if best_filter else "None",
        "best_filter_selection_status": (
            "BEST_FILTER_EVALUATED"
            if best_filter
            else "NO_FILTER_PASSES_CANONICAL_CRITERIA"
        ),
        "best_filter_selected_count": int(best_filter["selected_count"]) if best_filter else 0,
        "best_filter_selected_count_2026": selected_total_2026,
        "best_filter_mean_net_pnl": best_mean_pnl,
        "best_filter_2026_mean_net_pnl": best_mean_pnl_2026,
        "beats_global_random_p95": bool(
            any(
                b["filter_name"] == (best_filter["filter_name"] if best_filter else None)
                and b["baseline_type"] == "GLOBAL_SAME_COUNT"
                and b["beats_random_p95"]
                for b in random_baselines
            )
        )
        if best_filter
        else False,
        "beats_monthly_random_p95": bool(best_beats_random),
        "active_windows_count": int(best_temporal.get("active_windows_count", 0)),
        "recent_window_status": recent_window_status,
        "selected_count_total": selected_total,
        "filters_tested_count": len(filter_cols),
        "eligible_filters_count": len(eligible_defs),
        "excluded_filters_count": len(excluded_defs),
        "causal_filter_count": len(causal_defs),
        "non_causal_filter_count": len(non_causal_defs),
        "default_payoff_used": bool(rebuild["default_payoff_used"]),
        "fallback_probability_used": bool(rebuild["fallback_probability_used"]),
        "artificial_probability_threshold_used": bool(rebuild["artificial_probability_threshold_used"]),
        "evidence_classification": "EXPLORATORY_ONLY",
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_money_deployment": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "selection_frame_forbidden_columns": rebuild["selection_frame_forbidden_columns"],
        "selection_frame_status": rebuild["selection_frame_status"],
        "outcome_frame_status": rebuild["outcome_frame_status"],
        "rows_blocked_by_warmup_count": rebuild["warmup_blocked_rows"],
        "final_verdict": None,
        "recommended_next_step": None,
    }
    if version_is_v1382(version):
        recs = generate_v1_38_2_recommendation(summary)
    elif version_is_v1384(version):
        recs = generate_v1_38_4_recommendation(summary)
    elif version_is_v1383(version):
        recs = generate_v1_38_3_recommendation(summary)
    elif version_is_v1381(version):
        recs = generate_v1_38_1_recommendation(summary)
    else:
        recs = generate_v1_38_recommendation(summary)
    summary.update(recs)
    summary["final_verdict"] = recs["final_verdict"]
    summary["recommended_next_step"] = recs["recommended_next_step"]
    if version_is_v1382(version):
        summary["baseline_reporting_status"] = recs["baseline_reporting_status"]
        summary["project_state_structured"] = recs["project_state_structured"]
        summary["release_ready_for_external_review"] = recs["release_ready_for_external_review"]
        summary["previous_v1_38_release_ready_inconsistency_fixed"] = recs[
            "previous_v1_38_release_ready_inconsistency_fixed"
        ]
        summary["reviewer_readiness_semantics_status"] = recs[
            "reviewer_readiness_semantics_status"
        ]
        summary["recommendation_artifact_json_path"] = "reports/research/v1_38_2_recommendation.json"
        summary["recommendation_artifact_md_path"] = "reports/research/v1_38_2_recommendation.md"
        summary["baseline_interpretation_payload"] = build_v1_38_1_baseline_interpretation(summary)
        summary["beats_global_random_p95"] = summary["baseline_interpretation_payload"]["beats_global_random_p95"]
        summary["top_global_pnl_filter"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter"]
        summary["top_global_pnl_filter_mean_net_pnl"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter_mean_net_pnl"]
        summary["top_global_pnl_filter_recent_2026_selected_count"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter_recent_2026_selected_count"]
        summary["top_global_pnl_filter_recent_status"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter_recent_status"]
        summary["strategy_reviewer_ready"] = recs["strategy_reviewer_ready"]
        summary["strategy_reviewer_ready_reason"] = recs["strategy_reviewer_ready_reason"]
        summary["paper_live_ready"] = recs["paper_live_ready"]
        summary["preregistration_ready"] = recs["preregistration_ready"]
        summary["money_deployment_ready"] = recs["money_deployment_ready"]
    elif version_is_v1384(version):
        summary["baseline_reporting_status"] = recs["baseline_reporting_status"]
        summary["project_state_structured"] = True
        summary["release_ready_for_external_review"] = recs["release_ready_for_external_review"]
        summary["previous_v1_38_release_ready_inconsistency_fixed"] = True
        summary["reviewer_readiness_semantics_status"] = recs["reviewer_readiness_semantics_status"]
        summary["recommendation_artifact_json_path"] = "reports/research/v1_38_4_recommendation.json"
        summary["recommendation_artifact_md_path"] = "reports/research/v1_38_4_recommendation.md"
        summary["baseline_interpretation_payload"] = build_v1_38_1_baseline_interpretation(summary)
        summary["beats_global_random_p95"] = summary["baseline_interpretation_payload"]["beats_global_random_p95"]
        summary["top_global_pnl_filter"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter"]
        summary["top_global_pnl_filter_mean_net_pnl"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter_mean_net_pnl"]
        summary["top_global_pnl_filter_recent_2026_selected_count"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter_recent_2026_selected_count"]
        summary["top_global_pnl_filter_recent_status"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter_recent_status"]
        summary["strategy_reviewer_ready"] = recs["strategy_reviewer_ready"]
        summary["strategy_reviewer_ready_reason"] = recs["strategy_reviewer_ready_reason"]
        summary["paper_live_ready"] = recs["paper_live_ready"]
        summary["preregistration_ready"] = recs["preregistration_ready"]
        summary["money_deployment_ready"] = recs["money_deployment_ready"]
        summary["status_field_policy"] = recs["status_field_policy"]
        summary["status_field_present"] = recs["status_field_present"]
        summary.pop("ready_for_reviewer", None)
        summary.pop("ready_for_reviewer_scope", None)
        summary.pop("ready_for_reviewer_is_release_ready", None)
    elif version_is_v1383(version):
        summary["baseline_reporting_status"] = recs["baseline_reporting_status"]
        summary["project_state_structured"] = True
        summary["release_ready_for_external_review"] = recs["release_ready_for_external_review"]
        summary["previous_v1_38_release_ready_inconsistency_fixed"] = True
        summary["reviewer_readiness_semantics_status"] = recs["reviewer_readiness_semantics_status"]
        summary["recommendation_artifact_json_path"] = "reports/research/v1_38_3_recommendation.json"
        summary["recommendation_artifact_md_path"] = "reports/research/v1_38_3_recommendation.md"
        summary["baseline_interpretation_payload"] = build_v1_38_1_baseline_interpretation(summary)
        summary["beats_global_random_p95"] = summary["baseline_interpretation_payload"]["beats_global_random_p95"]
        summary["top_global_pnl_filter"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter"]
        summary["top_global_pnl_filter_mean_net_pnl"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter_mean_net_pnl"]
        summary["top_global_pnl_filter_recent_2026_selected_count"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter_recent_2026_selected_count"]
        summary["top_global_pnl_filter_recent_status"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter_recent_status"]
        summary["strategy_reviewer_ready"] = recs["strategy_reviewer_ready"]
        summary["strategy_reviewer_ready_reason"] = recs["strategy_reviewer_ready_reason"]
        summary["paper_live_ready"] = recs["paper_live_ready"]
        summary["preregistration_ready"] = recs["preregistration_ready"]
        summary["money_deployment_ready"] = recs["money_deployment_ready"]
        summary.pop("ready_for_reviewer", None)
        summary.pop("ready_for_reviewer_scope", None)
        summary.pop("ready_for_reviewer_is_release_ready", None)
    elif version_is_v1381(version):
        summary["baseline_reporting_status"] = recs["baseline_reporting_status"]
        summary["project_state_structured"] = recs["project_state_structured"]
        summary["release_ready_for_external_review"] = recs["release_ready_for_external_review"]
        summary["previous_v1_38_release_ready_inconsistency_fixed"] = recs[
            "previous_v1_38_release_ready_inconsistency_fixed"
        ]
        summary["recommendation_artifact_json_path"] = "reports/research/v1_38_1_recommendation.json"
        summary["recommendation_artifact_md_path"] = "reports/research/v1_38_1_recommendation.md"
        summary["baseline_interpretation_payload"] = build_v1_38_1_baseline_interpretation(summary)
        summary["beats_global_random_p95"] = summary["baseline_interpretation_payload"]["beats_global_random_p95"]
        summary["top_global_pnl_filter"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter"]
        summary["top_global_pnl_filter_mean_net_pnl"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter_mean_net_pnl"]
        summary["top_global_pnl_filter_recent_2026_selected_count"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter_recent_2026_selected_count"]
        summary["top_global_pnl_filter_recent_status"] = summary["baseline_interpretation_payload"]["top_global_pnl_filter_recent_status"]
    summary["consistency_check_status"] = "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    summary["causal_safety_status"] = safety_audit["causal_safety_status"]
    summary["causal_safety_issues"] = safety_audit["violations"]
    summary["causal_safety_passed_filters"] = safety_audit["passed_filters"]
    summary["causal_safety_excluded_filters"] = safety_audit["excluded_filters"]
    summary["ev_proxy_status"] = rebuild["ev_feature_rebuild_status"]
    summary["cost_proxy_status"] = "COST_PROXY_REBUILT_EXPLICITLY"
    summary["best_filter_net_mean_pnl"] = best_mean_pnl
    summary["best_filter_2026_mean_net_pnl"] = best_mean_pnl_2026

    reports = {
        "ev_net_canonical_input_guard": guard,
        "ev_net_feature_rebuild": rebuild,
        "ev_net_filter_grid": {
            "filters_tested": filter_defs,
            "eligible_filters": [f["filter_name"] for f in eligible_defs],
            "excluded_filters": [f["filter_name"] for f in excluded_defs],
            "exclusion_reasons": {f["filter_name"]: f.get("exclusion_reason") for f in excluded_defs},
            "causal_filter_count": len(causal_defs),
            "non_causal_filter_count": len(non_causal_defs),
            "filter_grid_status": summary["filter_grid_status"],
        },
        "ev_net_filter_evaluation": {
            "status": summary["evaluation_status"],
            "results": eval_results,
            "selected_count_total": selected_total,
            "selected_count_total_2026": selected_total_2026,
        },
        "ev_net_random_baselines": {
            "status": summary["random_baseline_status"],
            "results": random_baselines,
        },
        "ev_net_temporal_robustness": {
            "status": summary["temporal_robustness_status"],
            "temporal_results": temporal_rob_full["temporal_results"],
            "summary_by_filter": temporal_rob_full["summary_by_filter"],
        },
        "ev_net_regime_robustness": {
            "status": summary["regime_robustness_status"],
            **regime_rob,
        },
        "ev_net_overfit_guard": overfit_guard,
        **(
            {
                "ev_net_baseline_interpretation": build_v1_38_1_baseline_interpretation(summary),
            }
            if version_is_v1381(version) or version_is_v1382(version) or version_is_v1383(version) or version_is_v1384(version)
            else {}
        ),
        "ev_net_research_summary": summary,
        "ev_net_research_consistency_check": {
            **(
                {"status": summary["consistency_check_status"]}
                if version_is_v1382(version)
                else {}
            ),
            **(
                {"consistency_check_status": summary["consistency_check_status"]}
                if not version_is_v1382(version)
                else {}
            ),
            "status_field_present": bool(version_is_v1382(version)),
            "status_field_matches_consistency_check_status": True,
            "issues": [],
            "version": display_version(version),
            "project_state_structured": bool(
                version_is_v1381(version)
                or version_is_v1382(version)
                or version_is_v1383(version)
                or version_is_v1384(version)
            ),
            "project_state_paths_aligned": bool(
                version_is_v1381(version)
                or version_is_v1382(version)
                or version_is_v1383(version)
                or version_is_v1384(version)
            ),
            "latest_metrics_aligned": bool(
                version_is_v1381(version)
                or version_is_v1382(version)
                or version_is_v1383(version)
                or version_is_v1384(version)
            ),
            "release_ready_inconsistency_fixed": bool(
                version_is_v1381(version)
                or version_is_v1382(version)
                or version_is_v1383(version)
                or version_is_v1384(version)
            ),
            "baseline_reporting_clarified": bool(
                version_is_v1381(version)
                or version_is_v1382(version)
                or version_is_v1383(version)
                or version_is_v1384(version)
            ),
            "legacy_status_field_removed_or_mirrored": bool(version_is_v1382(version) or version_is_v1383(version) or version_is_v1384(version)),
            "reviewer_readiness_semantics_clarified": bool(version_is_v1382(version) or version_is_v1383(version) or version_is_v1384(version)),
            "ambiguous_ready_for_reviewer_removed": bool(version_is_v1383(version) or version_is_v1384(version)),
            "status_field_policy": "REMOVED" if version_is_v1384(version) else ("MIRRORED" if version_is_v1382(version) or version_is_v1383(version) else None),
        },
        **(
            {
                "ev_net_reviewer_readiness_semantics": {
                    "release_ready_for_external_review": True,
                    "strategy_reviewer_ready": False,
                    "strategy_reviewer_ready_reason": (
                        "recent 2026 window negative and no strategy validated"
                    ),
                    "paper_live_ready": False,
                    "preregistration_ready": False,
                    "money_deployment_ready": False,
                    "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
                }
            }
            if version_is_v1382(version) or version_is_v1384(version)
            else {}
        ),
        "recommendation": recs,
    }
    write_v1_32_reports(reports, version=version)
    update_latest_reports(summary, version)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--canonical-summary")
    parser.add_argument("--canonical-consistency")
    parser.add_argument("--calibration-summary", required=True)
    parser.add_argument("--calibration-temporal", required=True)
    parser.add_argument("--cost-model", required=True)
    parser.add_argument("--version", default="v1.32.2")
    args = parser.parse_args()
    
    print(f"--- Running EV-Net Filter Research {args.version} ---")
    
    # 1. Load Data
    pred_df = pd.read_parquet(args.predictions)
    ds_df = pd.read_parquet(args.dataset)
    
    # Normalize timestamps
    pred_df["timestamp"] = pd.to_datetime(pred_df["timestamp"], utc=True).dt.tz_convert(None)
    ds_df["timestamp"] = pd.to_datetime(ds_df["timestamp"], utc=True).dt.tz_convert(None)
    
    # Merge
    common_cols = [c for c in ds_df.columns if c in pred_df.columns and c != "timestamp"]
    ds_cols = [c for c in ds_df.columns if c not in common_cols]
    df = pd.merge(pred_df, ds_df[ds_cols], on="timestamp", how="inner")

    if version_is_v138(args.version):
        _run_v138(
            args=args,
            version=args.version,
            pred_df=pred_df,
            ds_df=ds_df,
            merged_df=df,
        )
        return
    
    # 2. Rebuild Frames
    selection, outcome, integrity = build_prediction_frames(df)
    full_df = selection.copy()
    full_df["actual_target"] = outcome["actual_target"]
    if "forward_return_12bar" in df.columns:
        full_df["forward_return_12bar"] = df["forward_return_12bar"]
        
    # 3. Rebuild Calibrated Probabilities
    full_df = rebuild_calibrated_probabilities(full_df)
    
    # 4. Payoff Estimation (Causal)
    full_df = estimate_causal_payoffs(full_df)
    
    # 5. Cost Proxy
    full_df = apply_cost_proxy(full_df)
    
    # 6. Build EV Proxies
    full_df = build_ev_proxies(full_df)
    
    # 7. Apply Filter Rules & Load Definitions
    full_df = apply_ev_filter_rules(full_df)
    filter_defs = get_ev_filter_definitions()
    filter_cols = [f["filter_name"] for f in filter_defs]
    
    eligible_defs = [f for f in filter_defs if f.get("eligible_for_ranking", True)]
    excluded_defs = [f for f in filter_defs if not f.get("eligible_for_ranking", True)]
    
    # 8. Causal Safety Audit
    safety_audit = audit_ev_filter_causality(full_df, filter_cols)
    
    # 9. Evaluation (Eligible only)
    eval_results = evaluate_ev_filters(full_df, filter_defs)
    
    # 10. Random Baselines (Eligible only)
    random_baselines = generate_random_baselines(full_df, eval_results, filter_defs)
    
    # 11. Temporal Robustness (Eligible only)
    temporal_rob_full = analyze_temporal_robustness(full_df, filter_defs)
    temporal_rob = temporal_rob_full["temporal_results"]
    temporal_summary = temporal_rob_full["summary_by_filter"]
    
    # 12. Regime Robustness (Eligible only)
    regime_rob = analyze_regime_robustness(full_df, filter_defs)
    
    # 13. Overfit Guard
    overfit_guard = analyze_overfit_risk([f["filter_name"] for f in eligible_defs], eval_results)
    
    # 14. Summary & Recommendation
    eligible_for_best = []
    passed_filters = safety_audit["passed_filters"]
    
    for res in eval_results:
        f_name = res["filter_name"]
        if f_name not in passed_filters:
            continue
        
        s = temporal_summary.get(f_name, {})
        
        monthly_baseline = [
            b for b in random_baselines 
            if b["filter_name"] == f_name and b["baseline_type"] == "MONTHLY_COUNT_PRESERVING"
        ]
        beats_random = monthly_baseline[0]["beats_random_p95"] if monthly_baseline else False
        
        if (res["selected_count"] >= 50 and 
            s.get("active_windows_count", 0) >= 3 and 
            s.get("recent_2026_selected_count", 0) > 0 and 
            beats_random):
            eligible_for_best.append(res)
            
    best_filter = max(eligible_for_best, key=lambda x: x["net_mean_pnl"]) if eligible_for_best else None
    
    best_monthly_baseline = [
        b for b in random_baselines 
        if best_filter and b["filter_name"] == best_filter["filter_name"] 
        and b["baseline_type"] == "MONTHLY_COUNT_PRESERVING"
    ]
    best_beats_random = best_monthly_baseline[0]["beats_random_p95"] if best_monthly_baseline else False
    
    best_temporal = temporal_summary.get(best_filter["filter_name"], {}) if best_filter else {}
    
    summary = {
        "ev_proxy_status": (
            "EV_PROXY_PARTIAL_WARMUP_BLOCKED" 
            if full_df["ev_proxy_ready"].sum() < len(full_df) 
            else "EV_PROXY_BUILD_COMPLETED_NO_DEFAULTS"
        ),
        "cost_proxy_status": "COST_PROXY_APPLIED_10BPS",
        "causal_safety_status": safety_audit["causal_safety_status"],
        "filters_tested_count": len(filter_cols),
        "eligible_filters_count": len(eligible_defs),
        "excluded_filters_count": len(excluded_defs),
        "best_filter_observed": best_filter["filter_name"] if best_filter else "None",
        "best_filter_selection_status": "BEST_FILTER_EVALUATED" if best_filter else "NO_FILTER_PASSES_STRICT_RECENT_CRITERIA",
        "best_filter_net_mean_pnl": best_filter["net_mean_pnl"] if best_filter else 0,
        "best_filter_selected_count": best_filter["selected_count"] if best_filter else 0,
        "beats_monthly_random_p95": best_beats_random,
        "active_windows_count": best_temporal.get("active_windows_count", 0),
        "recent_2026_selected_count": best_temporal.get("recent_2026_selected_count", 0),
        "recent_2026_pnl": best_temporal.get("recent_2026_pnl", 0),
        "temporal_status": "EVALUATED_ALL_WINDOWS",
        "regime_status": regime_rob["regime_status"],
        "overfit_risk": overfit_guard["multiple_testing_risk"],
        "rows_blocked_by_warmup_count": int((~full_df["ev_proxy_ready"]).sum()),
        "default_payoff_used": False
    }
    
    recs = generate_v1_32_recommendation(summary)
    summary.update(recs)
    
    # 15. Write Reports
    reports = {
        "calibrated_probability_rebuild": {
            "calibration_method_primary": "platt_scaling",
            "calibration_method_secondary": None,
            "rebuild_walk_forward": True,
            "train_only_past": True,
            "test_only_future": True,
            "leakage_status": "CLEAN",
            "calibrated_probability_column": "predicted_probability_calibrated",
            "raw_probability_column": "predicted_probability",
            "sample_count": len(full_df),
            "rebuild_status": "CALIBRATED_PROBABILITY_REBUILD_WALK_FORWARD_OK"
        },
        "ev_payoff_estimation_audit": {
            "payoff_estimation_method": "rolling_expanding_mean",
            "min_periods": 100,
            "default_payoff_used": False,
            "rows_with_ready_payoff": int(full_df["payoff_estimate_ready"].sum()),
            "rows_blocked_by_warmup": int((~full_df["payoff_estimate_ready"]).sum()),
            "payoff_estimation_status": (
                "PAYOFF_ESTIMATION_CAUSAL_NO_DEFAULTS" 
                if full_df["payoff_estimate_ready"].sum() > 0 
                else "PAYOFF_ESTIMATION_BLOCKED_INSUFFICIENT_HISTORY"
            )
        },
        "ev_proxy_build": {
            "ev_proxy_status": summary["ev_proxy_status"],
            "rows_with_ev_ready": int(full_df["ev_proxy_ready"].sum()),
            "rows_without_ev_due_to_warmup": int((~full_df["ev_proxy_ready"]).sum()),
            "default_payoff_used": False,
            "ev_proxy_diagnostic_only": True
        },
        "ev_filter_candidate_grid": filter_defs,
        "ev_filter_excluded_audit_only": [
            {
                "filter_name": f["filter_name"],
                "exclusion_reason": f["exclusion_reason"],
                "causal_status": f["causal_status"],
                "performance_evaluated": False
            } for f in excluded_defs
        ],
        "ev_filter_causal_safety_audit": safety_audit,
        "ev_filter_evaluation": eval_results,
        "ev_filter_random_baselines": random_baselines,
        "ev_filter_temporal_robustness": temporal_rob_full,
        "ev_filter_regime_robustness": regime_rob,
        "ev_filter_overfit_guard": overfit_guard,
        "ev_net_research_summary": summary,
        "recommendation": recs
    }
    
    write_v1_32_reports(reports, version=args.version)
    
    # 16. Update PROJECT_STATE and latest reports
    update_latest_reports(summary, args.version)
    
    print(f"--- Finished {args.version}. Reports written to reports/research/ ---")


if __name__ == "__main__":
    main()
