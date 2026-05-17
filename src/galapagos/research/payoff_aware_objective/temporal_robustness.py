"""Temporal robustness summaries for payoff-aware objective research."""
from __future__ import annotations

from typing import Any


def summarize_temporal_robustness(temporal_summary: dict[str, Any]) -> dict[str, Any]:
    """Normalize temporal robustness output into a reporting payload."""
    return {
        "temporal_robustness_status": temporal_summary.get("temporal_status", "PAYOFF_OBJECTIVE_TEMPORAL_ROBUSTNESS_FAILED"),
        "recent_window_status": temporal_summary.get("recent_window_status", "PAYOFF_OBJECTIVE_RECENT_WINDOW_WEAK"),
        "split_records": temporal_summary.get("split_records", []),
    }

