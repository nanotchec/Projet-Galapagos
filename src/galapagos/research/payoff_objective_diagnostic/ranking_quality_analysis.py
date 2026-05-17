"""Ranking quality diagnostics for payoff-objective failure."""
from __future__ import annotations

from typing import Any

def analyze_ranking_quality(payoff_summary: dict[str, Any], score_report: dict[str, Any], cost_report: dict[str, Any]) -> dict[str, Any]:
    beats_probability = bool(payoff_summary.get("beats_probability_baseline"))
    beats_ev_proxy = bool(payoff_summary.get("beats_ev_proxy_baseline"))
    best_2026_metric = float(payoff_summary.get("best_candidate_2026_metric", 0.0))
    spearman_2026 = float(score_report.get("spearman_2026", 0.0))
    if beats_probability and beats_ev_proxy and best_2026_metric <= 0:
        status = "RANKING_IMPROVES_RELATIVE_BASELINES_BUT_EDGE_NEGATIVE"
    elif spearman_2026 <= 0:
        status = "RANKING_QUALITY_DEGRADED_2026"
    else:
        status = "RANKING_DIAGNOSTIC_INCONCLUSIVE"
    return {
        "ranking_quality_status": status,
        "spearman_2026": spearman_2026,
        "beats_probability_baseline": beats_probability,
        "beats_ev_proxy_baseline": beats_ev_proxy,
        "best_candidate_2026_metric": best_2026_metric,
        "cost_vs_gross_status": cost_report.get("cost_vs_gross_status"),
    }

