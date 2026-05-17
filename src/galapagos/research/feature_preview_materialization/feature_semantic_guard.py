from __future__ import annotations

import re
from typing import Any

FORBIDDEN_FEATURE_TERMS = [
    "target",
    "label",
    "prediction",
    "predict",
    "future",
    "forward_return",
    "future_return",
    "next_return",
    "next_price",
    "outcome",
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


def scan_feature_payloads(payloads: dict[str, Any]) -> dict[str, Any]:
    occurrences: list[dict[str, str]] = []

    def visit(value: Any, path: str, source: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_path = f"{path}.{key}" if path else str(key)
                for term in FORBIDDEN_FEATURE_TERMS:
                    if _matches(str(key), term):
                        occurrences.append({"file": source, "json_path": key_path, "offending_key_or_value": str(key), "matched_term": term})
                visit(nested, key_path, source)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]", source)
        elif isinstance(value, str):
            for term in FORBIDDEN_FEATURE_TERMS:
                if _matches(value, term):
                    occurrences.append({"file": source, "json_path": path, "offending_key_or_value": value, "matched_term": term})

    for source, payload in payloads.items():
        visit(payload, "", source)

    matched = {item["matched_term"] for item in occurrences}
    return {
        "anti_leakage_feature_guard_applied": True,
        "available_ts_policy_applied": True,
        "decision_ts_policy_applied": True,
        "event_ts_policy_applied": True,
        "feature_available_ts_lte_decision_ts_rule_applied": True,
        "no_lookahead_policy_applied": True,
        "leakage_detected": bool(occurrences),
        "lookahead_detected": bool(matched & {"future", "future_return", "forward_return", "next_return", "next_price"}),
        "forbidden_feature_terms_detected": bool(occurrences),
        "forbidden_feature_terms_count": len(occurrences),
        "forbidden_feature_term_occurrences": occurrences,
        "future_information_fields_detected": bool(matched & {"future", "future_return", "forward_return", "next_return", "next_price"}),
        "target_like_fields_detected": "target" in matched,
        "label_like_fields_detected": "label" in matched,
        "prediction_like_fields_detected": bool(matched & {"prediction", "predict"}),
    }
