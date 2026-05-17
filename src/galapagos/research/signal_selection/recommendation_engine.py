"""Recommendation synthesis for V1.24."""
from __future__ import annotations

from typing import Any


def build_selection_recommendation(
    *,
    sweep: list[dict[str, Any]],
    confidence_verdicts: list[str],
    regime_verdicts: list[str],
    frequency_verdicts: list[str],
    leakage_audit: dict[str, Any] | None = None,
    walk_forward_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    viable = [
        row
        for row in sweep
        if row.get("rule_name") != "no_trade" and row.get("selected_count", 0) > 0
        and row.get("causal", True)
    ]
    best = max(
        viable,
        key=lambda r: (
            r.get("net_mean_pnl_pct", -999),
            r.get("selected_count", 0) >= 30,
            r.get("beats_random_p95", False),
        ),
        default={},
    )
    best_verdict = best.get("verdict", ["NO_FILTER_FOUND"])
    any_positive = any(row.get("net_mean_pnl_pct", 0) > 0 for row in viable)
    any_random_p95 = any(row.get("beats_random_p95", False) for row in viable)
    recommendations = [
        "Do not activate LLM reviewer.",
        "Do not execute holdout.",
        "Do not trade live.",
    ]
    if any_positive and any_random_p95:
        recommendations.insert(0, "Continue with stricter signal selection research.")
        recommendations.insert(1, "Build cost-aware candidate gate offline only.")
    elif any_positive:
        recommendations.insert(
            0,
            "Test candidate gate with larger sample and same-count random baseline.",
        )
    else:
        recommendations.insert(0, "Need stronger alpha features before reviewer.")
        recommendations.insert(1, "Revisit cost assumptions but do not optimize exits yet.")
    return {
        "best_filter_observed": best.get("rule_name"),
        "best_policy_observed": best.get("policy"),
        "best_causal_filter": best.get("rule_name"),
        "best_causal_policy": best.get("policy"),
        "selected_count": best.get("selected_count", 0),
        "net_mean_pnl_pct": best.get("net_mean_pnl_pct", 0.0),
        "random_same_count_mean": best.get("random_same_count_mean"),
        "beats_random_p95": best.get("beats_random_p95", False),
        "best_filter_verdict": best_verdict,
        "cost_aware_verdict": _cost_verdict(best, any_positive, any_random_p95),
        "confidence_verdicts": confidence_verdicts,
        "regime_verdicts": regime_verdicts,
        "frequency_verdicts": frequency_verdicts,
        "leakage_audit_status": (leakage_audit or {}).get("status", "NOT_RUN"),
        "leakage_risk_resolved_for_causal_rules": bool(
            (leakage_audit or {}).get("leakage_risk_resolved_for_causal_rules", True)
        ),
        "walk_forward_verdict": (walk_forward_summary or {}).get(
            "walk_forward_verdict", "NOT_RUN"
        ),
        "low_frequency_strict_score_remains_promising": bool(
            (walk_forward_summary or {}).get("low_frequency_strict_score_remains_promising", False)
        ),
        "recommendations": recommendations,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True,
    }


def _cost_verdict(best: dict[str, Any], any_positive: bool, any_random_p95: bool) -> list[str]:
    verdicts = ["COST_AWARE_SIGNAL_SELECTION_COMPLETED"]
    if not best:
        return [*verdicts, "NO_FILTER_FOUND"]
    if best.get("selected_count", 0) < 30:
        verdicts.append("SAMPLE_TOO_SMALL")
    if not any_positive:
        verdicts.append("NO_FILTER_SURVIVES_COSTS")
    elif not any_random_p95:
        verdicts.append("PROMISING_BUT_NOT_DISTINGUISHABLE_FROM_RANDOM")
    else:
        verdicts.append("PROMISING_BUT_UNVALIDATED")
    return verdicts
