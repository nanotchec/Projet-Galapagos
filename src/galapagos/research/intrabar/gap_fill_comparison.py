"""Component to compare gap fill impact across versions."""
from __future__ import annotations

from typing import Any


def compare_gap_impact(prev: dict[str, Any], curr: dict[str, Any]) -> dict[str, Any]:
    """Compare gap impact metrics."""
    return {
        "previous_gap_ratio": prev.get("trade_candidates_gap_ratio"),
        "current_gap_ratio": curr.get("trade_candidates_gap_ratio"),
        "gap_ratio_reduction": (prev.get("trade_candidates_gap_ratio", 0) - 
                               curr.get("trade_candidates_gap_ratio", 0)),
        "previous_gap_candidates": prev.get("trade_candidates_in_gap"),
        "current_gap_candidates": curr.get("trade_candidates_in_gap")
    }

def compare_ledger_metrics(prev: dict[str, Any], curr: dict[str, Any]) -> dict[str, Any]:
    """Compare evaluation coverage and verdicts."""
    return {
        "previous_evaluated_ratio": prev.get("evaluated_ratio"),
        "current_evaluated_ratio": curr.get("evaluated_ratio"),
        "coverage_increase": (curr.get("evaluated_ratio", 0) - 
                             prev.get("evaluated_ratio", 0)),
        "previous_verdict": prev.get("comparison", {}).get("verdict"),
        "current_verdict": curr.get("comparison", {}).get("verdict")
    }
