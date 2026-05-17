from __future__ import annotations


def summarize_derivatives(derivatives: dict) -> dict:
    return {
        key: value.get("status", "missing")
        for key, value in derivatives.items()
        if isinstance(value, dict)
    }

