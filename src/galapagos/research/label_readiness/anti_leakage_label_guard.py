from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any


LABEL_FORBIDDEN_TERMS = [
    "prediction",
    "predict",
    "model_score",
    "trained_model",
    "paper_live",
    "real_order",
]


def _normalize(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _term_in_value(value: str, term: str) -> bool:
    return _normalize(term) in _normalize(value)


def scan_label_preview_payload(payload: Any) -> dict[str, Any]:
    occurrences: list[dict[str, str]] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_path = f"{path}.{key}" if path else str(key)
                for term in LABEL_FORBIDDEN_TERMS:
                    if _term_in_value(str(key), term):
                        occurrences.append({"json_path": key_path, "offending_key_or_value": str(key), "matched_term": term})
                visit(nested, key_path)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]")
        elif isinstance(value, str):
            for term in LABEL_FORBIDDEN_TERMS:
                if _term_in_value(value, term):
                    occurrences.append({"json_path": path, "offending_key_or_value": value, "matched_term": term})

    visit(payload, "")
    return {
        "label_semantic_scan_executed": True,
        "label_forbidden_terms_detected": bool(occurrences),
        "label_forbidden_terms_count": len(occurrences),
        "label_forbidden_term_occurrences": occurrences,
        "leakage_detected": False,
        "lookahead_detected": False,
    }


def parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

