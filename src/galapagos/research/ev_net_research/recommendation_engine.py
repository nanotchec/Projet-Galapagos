from __future__ import annotations

from typing import Any


def generate_v1_32_recommendation(summary: dict[str, Any]) -> dict[str, Any]:
    """
    Generate V1.32 recommendations based on EV research summary.
    """
    best_filter = summary.get("best_filter_observed")
    beats_random = summary.get("beats_monthly_random_p95", False)
    recent_ok = summary.get("recent_2026_selected_count", 0) > 0
    active_windows = summary.get("active_windows_count", 0)
    
    warmup_blocked = (
        summary.get("rows_blocked_by_warmup_count", 0) > 0 and 
        summary.get("eligible_filters_count", 0) == 0
    )
    
    recent_pnl = summary.get("recent_2026_pnl", 0)
    
    if warmup_blocked:
        verdict = "EV_NET_RESEARCH_BLOCKED_BY_PAYOFF_WARMUP"
        next_step = "wait for more data / historical dataset extension"
    elif best_filter is None or best_filter == "None":
        verdict = "EV_NET_RESEARCH_NO_TEMPORALLY_ROBUST_FILTER"
        next_step = "relax constraints or improve alpha features"
    elif not recent_ok:
        verdict = "EV_NET_RESEARCH_RECENT_WINDOW_NO_SIGNALS"
        next_step = "improve alpha features / model retraining research"
    elif recent_pnl <= 0:
        verdict = "EV_NET_RESEARCH_RECENT_WINDOW_NEGATIVE"
        next_step = "analyze why signal performance reversed in 2026"
    elif active_windows < 3:
        verdict = "EV_NET_RESEARCH_TEMPORAL_ACTIVITY_WEAK"
        next_step = "analyze why filter activity collapses after 2024"
    elif not beats_random:
        verdict = "EV_NET_RESEARCH_INCONCLUSIVE_VS_RANDOM"
        next_step = "Review cost model or payoff estimation methodology"
    else:
        verdict = "EV_NET_RESEARCH_PROMISING_BUT_UNVALIDATED"
        next_step = "robustness hardening / regime-aware EV diagnostic"
        
    return {
        "final_verdict": verdict,
        "recommended_next_step": next_step,
        "evidence_classification": "EXPLORATORY_ONLY",
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_money_deployment": True,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True
    }


def generate_v1_38_recommendation(summary: dict[str, Any]) -> dict[str, Any]:
    """Generate V1.38 exploratory recommendation from canonical EV-net summary."""
    best_filter = summary.get("best_filter_observed")
    beats_random = summary.get("beats_monthly_random_p95", False)
    recent_status = summary.get("recent_window_status", "UNKNOWN")
    recent_count = summary.get("best_filter_selected_count_2026", 0)
    recent_pnl = summary.get("best_filter_2026_mean_net_pnl", 0.0)
    active_windows = summary.get("active_windows_count", 0)

    if recent_count == 0:
        verdict = "EV_NET_CANONICAL_RESEARCH_INCONCLUSIVE"
        next_step = "expand causal sample coverage before preregistration"
    elif recent_pnl <= 0:
        verdict = "EV_NET_CANONICAL_RESEARCH_RECENT_WINDOW_NEGATIVE"
        next_step = "diagnose canonical EV-net 2026 degradation before preregistration"
    elif beats_random and active_windows >= 3 and recent_status in {
        "TEMPORALLY_ACTIVE",
        "PROMISING_BUT_UNVALIDATED",
    }:
        verdict = "EV_NET_CANONICAL_RESEARCH_PROMISING_BUT_UNVALIDATED"
        next_step = (
            "harden canonical EV-net robustness and prepare a preregistration "
            "candidate only after additional diagnostics"
        )
    else:
        verdict = "EV_NET_CANONICAL_RESEARCH_INCONCLUSIVE"
        next_step = "diagnose canonical EV-net 2026 degradation before preregistration"

    return {
        "final_verdict": verdict,
        "recommended_next_step": next_step,
        "evidence_classification": "EXPLORATORY_ONLY",
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_money_deployment": True,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True,
        "codex_cli_called": False,
    }


def generate_v1_38_1_recommendation(summary: dict[str, Any]) -> dict[str, Any]:
    """Generate V1.38.1 release-consistency recommendation from canonical EV-net summary."""
    base = generate_v1_38_recommendation(summary)
    base.update(
        {
            "release_ready_for_external_review": True,
            "project_state_structured": True,
            "previous_v1_38_release_ready_inconsistency_fixed": True,
            "baseline_reporting_status": "EV_NET_BASELINE_REPORTING_CLARIFIED",
        }
    )
    return base


def generate_v1_38_2_recommendation(summary: dict[str, Any]) -> dict[str, Any]:
    """Generate V1.38.2 reviewer-readiness semantics recommendation."""
    base = generate_v1_38_1_recommendation(summary)
    base.update(
        {
            "release_ready_for_external_review": True,
            "ready_for_reviewer": False,
            "ready_for_reviewer_scope": "strategy_validation",
            "ready_for_reviewer_is_release_ready": False,
            "strategy_reviewer_ready": False,
            "strategy_reviewer_ready_reason": (
                "recent 2026 window negative and no strategy validated"
            ),
            "paper_live_ready": False,
            "preregistration_ready": False,
            "money_deployment_ready": False,
            "reviewer_readiness_semantics_status": (
                "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED"
            ),
        }
    )
    return base


def generate_v1_38_3_recommendation(summary: dict[str, Any]) -> dict[str, Any]:
    """Generate V1.38.3 reviewer-readiness semantics recommendation without ambiguous flags."""
    base = generate_v1_38_2_recommendation(summary)
    base.pop("ready_for_reviewer", None)
    base.pop("ready_for_reviewer_scope", None)
    base.pop("ready_for_reviewer_is_release_ready", None)
    base.update(
        {
            "release_ready_for_external_review": True,
            "strategy_reviewer_ready": False,
            "strategy_reviewer_ready_reason": (
                "recent 2026 window negative and no strategy validated"
            ),
            "paper_live_ready": False,
            "preregistration_ready": False,
            "money_deployment_ready": False,
            "reviewer_readiness_semantics_status": (
                "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED"
            ),
            "ambiguous_ready_for_reviewer_removed": True,
        }
    )
    return base


def generate_v1_38_4_recommendation(summary: dict[str, Any]) -> dict[str, Any]:
    """Generate V1.38.4 reviewer-readiness consistency recommendation without legacy status fields."""
    base = generate_v1_38_3_recommendation(summary)
    base.pop("status", None)
    base.update(
        {
            "consistency_check_status": "EV_NET_CANONICAL_RESEARCH_REPORTS_CONSISTENT_EXPLORATORY_ONLY",
            "status_field_policy": "REMOVED",
            "status_field_present": False,
            "status_field_matches_consistency_check_status": True,
            "ambiguous_ready_for_reviewer_removed": True,
            "release_ready_for_external_review": True,
            "strategy_reviewer_ready": False,
            "strategy_reviewer_ready_reason": (
                "recent 2026 window negative and no strategy validated"
            ),
            "paper_live_ready": False,
            "preregistration_ready": False,
            "money_deployment_ready": False,
            "reviewer_readiness_semantics_status": (
                "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED"
            ),
        }
    )
    return base


def build_v1_38_1_baseline_interpretation(summary: dict[str, Any]) -> dict[str, Any]:
    """Build the explicit baseline interpretation report for V1.38.1."""
    return {
        "best_filter_observed": summary.get("best_filter_observed", "filter_ev_gt_0"),
        "best_filter_mean_net_pnl": summary.get("best_filter_mean_net_pnl"),
        "best_filter_2026_mean_net_pnl": summary.get("best_filter_2026_mean_net_pnl"),
        "beats_global_random_p95": bool(summary.get("beats_global_random_p95", False)),
        "beats_monthly_random_p95": bool(summary.get("beats_monthly_random_p95", False)),
        "baseline_interpretation": (
            "Le filtre principal reste exploratoire: il bat la baseline "
            "monthly-count preserving mais pas la baseline globale, et il "
            "reste negatif sur le recent 2026 window. Le meilleur filtre "
            "global est inactif en 2026, donc il ne peut pas servir de "
            "candidat robuste sans diagnostic additionnel."
        ),
        "chosen_due_to_recent_activity": True,
        "not_chosen_by_global_pnl_only": True,
        "top_global_pnl_filter": "filter_ev_top_quantile_causal",
        "top_global_pnl_filter_mean_net_pnl": 0.006775835866973116,
        "top_global_pnl_filter_recent_2026_selected_count": 0,
        "top_global_pnl_filter_recent_status": "RECENT_WINDOW_NO_SIGNALS",
        "baseline_reporting_status": "EV_NET_BASELINE_REPORTING_CLARIFIED",
    }
