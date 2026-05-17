"""Verdict logic for payoff-aware objective research."""
from __future__ import annotations

from typing import Any


def build_research_verdict(summary: dict[str, Any]) -> dict[str, Any]:
    """Return a conservative research verdict and the next step."""
    if summary.get("input_guard_status") != "PAYOFF_OBJECTIVE_INPUT_GUARD_PASSED":
        return {
            "final_verdict": "PAYOFF_OBJECTIVE_RESEARCH_FAILED",
            "recommended_next_step": "fix input guard and report alignment before further research",
        }
    if summary.get("recent_window_status") == "RECENT_WINDOW_WEAK":
        return {
            "final_verdict": "PAYOFF_OBJECTIVE_RESEARCH_RECENT_WINDOW_WEAK",
            "recommended_next_step": "diagnose why payoff-aware objective still fails recent 2026 window",
        }
    if summary.get("beats_probability_baseline") or summary.get("beats_ev_proxy_baseline"):
        return {
            "final_verdict": "PAYOFF_OBJECTIVE_RESEARCH_PROMISING_BUT_UNVALIDATED",
            "recommended_next_step": (
                "harden payoff-aware objective diagnostics and run ablation tests, still exploratory only"
            ),
        }
    return {
        "final_verdict": "PAYOFF_OBJECTIVE_RESEARCH_INCONCLUSIVE",
        "recommended_next_step": "improve payoff labels and feature diagnostics before further objective research",
    }

