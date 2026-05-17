from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def analyze_risk_rejections(backtest_results: list[dict[str, Any]]) -> dict[str, Any]:
    rejected: list[dict[str, Any]] = []
    by_profile: Counter[str] = Counter()
    by_strategy: Counter[str] = Counter()
    by_reason: Counter[str] = Counter()

    for result in backtest_results:
        run_id = str(result.get("run_id", "unknown"))
        for profile, raw in result.get("raw_results", {}).items():
            for decision in raw.get("decisions", []):
                if decision.get("risk_approved", True):
                    continue
                item = {
                    "run_id": run_id,
                    "profile": decision.get("profile") or profile,
                    "strategy": decision.get("strategy") or "unknown",
                    "decision": decision.get("decision"),
                    "timestamp": decision.get("decision_timestamp") or decision.get("timestamp"),
                    "reasons": list(decision.get("risk_reasons") or []),
                    "replay_index": decision.get("replay_index"),
                }
                rejected.append(item)
                by_profile[item["profile"]] += 1
                by_strategy[item["strategy"]] += 1
                for reason in item["reasons"] or ["unspecified"]:
                    by_reason[reason] += 1

    recommendations = _recommendations(by_reason)
    return {
        "total_rejections": len(rejected),
        "rejections_by_profile": dict(by_profile),
        "rejections_by_strategy": dict(by_strategy),
        "rejections_by_reason": dict(by_reason),
        "top_10_reasons": by_reason.most_common(10),
        "examples": rejected[:10],
        "recommendations": recommendations,
    }


def summarize_rejections_by_run(backtest_results: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for result in backtest_results:
        run_id = str(result.get("run_id", "unknown"))
        profile_counts: dict[str, int] = defaultdict(int)
        for profile, raw in result.get("raw_results", {}).items():
            profile_counts[profile] += sum(
                1
                for decision in raw.get("decisions", [])
                if not decision.get("risk_approved", True)
            )
        output[run_id] = dict(profile_counts)
    return output


def _recommendations(by_reason: Counter[str]) -> list[str]:
    recommendations: list[str] = []
    if by_reason.get("Max total exposure fraction exceeded"):
        recommendations.append(
            "Analyser la taille des positions et la limite max_total_exposure_fraction."
        )
    if by_reason.get("Open position already exists for this profile and asset"):
        recommendations.append(
            "Verifier si la policy tente d'empiler trop souvent des positions sur le meme profil."
        )
    if by_reason.get("Max open positions per profile reached"):
        recommendations.append("Comparer la frequence des signaux avec la limite de positions.")
    if by_reason.get("risk_fraction exceeds max_risk_per_trade"):
        recommendations.append("Aligner la policy mock avec max_risk_per_trade.")
    if not recommendations:
        recommendations.append(
            "Inspecter les decisions refusees et ajouter des compteurs par raison "
            "dans les prochains runs."
        )
    return recommendations
