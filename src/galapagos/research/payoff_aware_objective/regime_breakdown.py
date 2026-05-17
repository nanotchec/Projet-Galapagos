"""Regime breakdown for payoff-aware objective research."""
from __future__ import annotations

from typing import Any


def summarize_regime_breakdown(regime_summary: dict[str, Any]) -> dict[str, Any]:
    """Normalize regime breakdown output into a reporting payload."""
    return {
        "regime_breakdown_status": regime_summary.get("regime_breakdown_status", "PAYOFF_OBJECTIVE_REGIME_DATA_LIMITED"),
        "regime_column": regime_summary.get("regime_column"),
        "rows": regime_summary.get("rows", []),
    }

