from __future__ import annotations


def derivatives_filter(derivatives_summary: dict) -> dict:
    unavailable = [key for key, status in derivatives_summary.items() if status != "available"]
    return {
        "strategy": "derivatives_signal",
        "enabled": not unavailable,
        "unavailable": unavailable,
        "status": "degraded" if unavailable else "available",
    }

