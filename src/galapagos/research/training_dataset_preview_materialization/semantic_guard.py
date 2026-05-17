from __future__ import annotations

import re
from typing import Any

FORBIDDEN_TRAINING_PREVIEW_TERMS = [
    "prediction",
    "predict",
    "model",
    "training_signal",
    "signal",
    "strategy",
    "trade_signal",
    "order",
    "real_order",
    "execution",
    "backtest",
    "pnl",
    "profit",
    "ev",
    "expected_value",
    "mfe",
    "mae",
    "win",
    "loss",
    "hit_tp",
    "hit_sl",
]


def _normalize(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _matches(value: str, term: str) -> bool:
    normalized = _normalize(value)
    normalized_term = _normalize(term)
    if normalized_term in {"ev", "win"}:
        return bool(re.search(rf"(^|_){normalized_term}($|_)", normalized))
    return normalized_term in normalized


def scan_training_preview_payloads(payloads: dict[str, Any]) -> dict[str, Any]:
    occurrences: list[dict[str, str]] = []

    def visit(value: Any, path: str, source: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_path = f"{path}.{key}" if path else str(key)
                for term in FORBIDDEN_TRAINING_PREVIEW_TERMS:
                    if _matches(str(key), term):
                        occurrences.append({"file": source, "json_path": key_path, "offending_key_or_value": str(key), "matched_term": term})
                visit(nested, key_path, source)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]", source)
        elif isinstance(value, str):
            for term in FORBIDDEN_TRAINING_PREVIEW_TERMS:
                if _matches(value, term):
                    occurrences.append({"file": source, "json_path": path, "offending_key_or_value": value, "matched_term": term})

    for source, payload in payloads.items():
        visit(payload, "", source)
    matched = {item["matched_term"] for item in occurrences}
    return {
        "forbidden_training_preview_terms_detected": bool(occurrences),
        "forbidden_training_preview_terms_count": len(occurrences),
        "forbidden_training_preview_term_occurrences": occurrences,
        "prediction_like_fields_detected": bool(matched & {"prediction", "predict"}),
        "model_training_terms_detected": "model" in matched,
        "backtest_terms_detected": "backtest" in matched,
        "trading_signal_terms_detected": bool(matched & {"signal", "strategy", "trade_signal", "training_signal"}),
        "order_execution_terms_detected": bool(matched & {"order", "real_order", "execution"}),
    }
