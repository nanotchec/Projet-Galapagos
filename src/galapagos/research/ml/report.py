"""ML lab report generation."""
from __future__ import annotations

from typing import Any


def ml_verdict(results: list[dict]) -> str:
    """Derive overall ML verdict from walk-forward results."""
    if not results:
        return "ML_NEEDS_MORE_DATA"
    any_beats_random = False
    for r in results:
        for w in r.get("windows", []):
            m = w.get("metrics", {})
            if m.get("beats_random"):
                any_beats_random = True
    if not any_beats_random:
        return "ML_NO_EDGE"
    return "ML_BEATS_RANDOM_BUT_NOT_COSTS"


def build_ml_summary(
    results: list[dict], *, sklearn_available: bool, dataset_report: dict,
) -> dict[str, Any]:
    """Build the main ML lab summary."""
    verdict = ml_verdict(results)
    best: dict[str, Any] = {}
    best_score = -1.0
    for r in results:
        for w in r.get("windows", []):
            m = w.get("metrics", {})
            # Prefer results that beat random; use balanced_accuracy as tiebreaker
            score = m.get("balanced_accuracy", 0)
            if m.get("beats_random"):
                score += 1.0
            key = f"{r.get('target')}_{r.get('model')}_{w.get('window')}"
            if score > best_score:
                best_score = score
                best = {"key": key, "accuracy": m.get("accuracy", 0),
                        "balanced_accuracy": m.get("balanced_accuracy", 0),
                        "beats_random": m.get("beats_random", False),
                        "target": r.get("target"),
                        "model": r.get("model"),
                        "feature_set": r.get("feature_set"),
                        "window": w.get("window"),
                        "metrics": m}
    return {
        "version": "V1.15",
        "sklearn_available": sklearn_available,
        "dataset": dataset_report,
        "total_experiments": len(results),
        "verdict": verdict,
        "best_result": best,
        "llm_reviewer_ready": verdict in (
            "ML_BEATS_ALPHA_SCORE", "ML_READY_FOR_REVIEWER_EXPERIMENT",
        ),
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False,
    }
