from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean, pstdev
from typing import Any


def analyze_decision_stability(repetitions: list[dict[str, Any]]) -> dict[str, Any]:
    if len(repetitions) < 2:
        return {
            "repetition_count": len(repetitions),
            "global": {},
            "windows": {},
            "verdict": "INSUFFICIENT_REPETITIONS",
        }
    windows = sorted({window for rep in repetitions for window in rep.get("windows", {})})
    window_results = {
        window: _analyze_window(
            [rep["windows"][window] for rep in repetitions if window in rep["windows"]]
        )
        for window in windows
    }
    all_reviews = []
    for rep in repetitions:
        for window, payload in rep.get("windows", {}).items():
            for review in payload.get("reviews", []):
                all_reviews.append({**review, "window": window, "repetition": rep["index"]})
    global_result = _agreement_metrics(all_reviews)
    pnl_by_window = {
        window: [
            float(rep["windows"][window].get("final_equity_pnl") or 0.0)
            for rep in repetitions
            if window in rep["windows"]
        ]
        for window in windows
    }
    global_result["pnl_by_window"] = {
        window: _variance(values) for window, values in pnl_by_window.items()
    }
    verdict = stability_verdict(global_result)
    return {
        "repetition_count": len(repetitions),
        "global": global_result,
        "windows": window_results,
        "verdict": verdict,
    }


def stability_verdict(metrics: dict[str, Any]) -> str:
    rate = float(metrics.get("exact_decision_match_rate") or 0.0)
    if rate >= 0.85:
        return "STABLE"
    if rate >= 0.6:
        return "MODERATELY_UNSTABLE"
    return "HIGHLY_UNSTABLE"


def _analyze_window(reports: list[dict[str, Any]]) -> dict[str, Any]:
    reviews = []
    for index, report in enumerate(reports, start=1):
        for review in report.get("reviews", []):
            reviews.append({**review, "repetition": index, "window": report.get("window_label")})
    metrics = _agreement_metrics(reviews)
    pnl = [float(report.get("final_equity_pnl") or 0.0) for report in reports]
    trades = [int(report.get("ledger_trade_count") or 0) for report in reports]
    metrics["pnl_variance"] = _variance(pnl)
    metrics["trade_count_variance"] = _variance([float(value) for value in trades])
    metrics["pnl_by_repetition"] = pnl
    metrics["trade_count_by_repetition"] = trades
    metrics["decision_distribution_by_repetition"] = [
        report.get("decision_distribution", {}) for report in reports
    ]
    return metrics


def _agreement_metrics(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for review in reviews:
        grouped[_candidate_key(review)].append(review)
    per_candidate = {}
    exact_matches = 0
    comparable = 0
    active_stable = 0
    active_comparable = 0
    flips = 0
    setup_matches = 0
    confidence_stds = []
    risk_stds = []
    unstable_examples = []
    for key, items in grouped.items():
        if len(items) < 2:
            continue
        comparable += 1
        decisions = [str(item.get("decision")) for item in items]
        setup = [_setup_quality(item) for item in items]
        active = [decision in {"LONG", "SHORT"} for decision in decisions]
        confidence = [_payload_float(item, "confidence") for item in items]
        risk = [_payload_float(item, "risk_fraction") for item in items]
        decision_counts = Counter(decisions)
        agreement = max(decision_counts.values()) / len(decisions)
        exact = len(decision_counts) == 1
        if exact:
            exact_matches += 1
        if len(set(setup)) == 1:
            setup_matches += 1
        if any(active):
            active_comparable += 1
            if len(set(active)) == 1:
                active_stable += 1
        if {"LONG", "NO_TRADE"}.issubset(set(decisions)):
            flips += 1
        confidence_stds.append(pstdev(confidence) if len(confidence) > 1 else 0.0)
        risk_stds.append(pstdev(risk) if len(risk) > 1 else 0.0)
        per_candidate[key] = {
            "decisions": decisions,
            "decision_agreement_rate": agreement,
            "setup_quality": setup,
            "confidence_std": confidence_stds[-1],
            "risk_fraction_std": risk_stds[-1],
        }
        if not exact and len(unstable_examples) < 10:
            unstable_examples.append({"candidate_key": key, **per_candidate[key]})
    return {
        "candidate_count": comparable,
        "decision_agreement_rate_mean": (
            mean(item["decision_agreement_rate"] for item in per_candidate.values())
            if per_candidate
            else 0.0
        ),
        "exact_decision_match_rate": exact_matches / comparable if comparable else 0.0,
        "active_decision_stability": (
            active_stable / active_comparable if active_comparable else 1.0
        ),
        "long_no_trade_flip_count": flips,
        "setup_quality_agreement_rate": setup_matches / comparable if comparable else 0.0,
        "confidence_std_mean": mean(confidence_stds) if confidence_stds else 0.0,
        "risk_fraction_std_mean": mean(risk_stds) if risk_stds else 0.0,
        "unstable_examples": unstable_examples,
        "per_candidate": per_candidate,
    }


def _candidate_key(review: dict[str, Any]) -> str:
    candidate = review.get("candidate") or {}
    return "|".join(
        [
            str(candidate.get("context_index")),
            str(candidate.get("baseline_policy")),
            str(candidate.get("baseline_decision")),
            str(candidate.get("current_price")),
        ]
    )


def _setup_quality(review: dict[str, Any]) -> str:
    payload = _raw_payload(review)
    return str(payload.get("setup_quality") or "unknown")


def _payload_float(review: dict[str, Any], key: str) -> float:
    value = _raw_payload(review).get(key)
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _raw_payload(review: dict[str, Any]) -> dict[str, Any]:
    import json

    raw = review.get("raw_response")
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _variance(values: list[float]) -> dict[str, Any]:
    return {
        "values": values,
        "mean": mean(values) if values else 0.0,
        "std": pstdev(values) if len(values) > 1 else 0.0,
        "min": min(values) if values else 0.0,
        "max": max(values) if values else 0.0,
    }
