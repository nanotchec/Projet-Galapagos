from __future__ import annotations

from typing import Any


def build_diagnostic_verdict(decomposition: dict[str, Any], rebuild: dict[str, Any]) -> dict[str, Any]:
    if not rebuild.get("count_match_v1_38_4", False):
        return {
            "final_verdict": "EV_DEGRADATION_REBUILD_MISMATCH",
            "recommended_next_step": "fix rebuild alignment before interpretation",
        }
    primary = decomposition.get("primary_driver")
    secondary = decomposition.get("secondary_drivers", [])
    if not primary:
        return {
            "final_verdict": "EV_DEGRADATION_INCONCLUSIVE",
            "recommended_next_step": "improve diagnostic data and logging",
        }
    if len(secondary) >= 2:
        verdict = "EV_DEGRADATION_MULTI_FACTOR"
    else:
        verdict = "EV_DEGRADATION_DRIVER_IDENTIFIED"
    next_step = "research payoff-aware EV model objective" if primary == "EV_PROXY_OVERESTIMATES_2026" else "improve diagnostic data and logging"
    return {
        "final_verdict": verdict,
        "recommended_next_step": next_step,
    }
