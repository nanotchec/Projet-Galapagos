from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .physical_auditor import V1_92_FILES

FORBIDDEN_SEED_FIELD_TERMS = [
    "target",
    "label",
    "prediction",
    "predict",
    "future_return",
    "future_ret",
    "future_price",
    "future_pnl",
    "future_profit",
    "pnl",
    "profit",
    "return_forward",
    "forward_return",
    "next_return",
    "next_price",
    "outcome",
    "realized_return",
    "realized_pnl",
    "ev",
    "expected_value",
    "mfe",
    "mae",
    "drawdown_after",
    "hit_tp",
    "hit_sl",
    "win",
    "loss",
]

TARGET_LIKE_TERMS = {"target", "outcome", "hit_tp", "hit_sl", "win", "loss"}
FUTURE_LIKE_TERMS = {
    "future_return",
    "future_ret",
    "future_price",
    "future_pnl",
    "future_profit",
    "return_forward",
    "forward_return",
    "next_return",
    "next_price",
    "realized_return",
    "realized_pnl",
    "drawdown_after",
}
LABEL_LIKE_TERMS = {"label"}
PREDICTION_LIKE_TERMS = {"prediction", "predict"}


def scan_physical_seed_semantics(project_root: Path) -> dict[str, Any]:
    occurrences: list[dict[str, str]] = []
    for rel_path in V1_92_FILES:
        path = project_root / rel_path
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            occurrences.append(
                {
                    "file": str(rel_path),
                    "json_path": "$",
                    "offending_key_or_value": f"invalid_json:{exc}",
                    "matched_term": "invalid_json",
                }
            )
            continue
        _scan_node(payload, file=str(rel_path), json_path="$", occurrences=occurrences)

    matched_terms = {item["matched_term"] for item in occurrences}
    return {
        "physical_seed_semantic_scan_executed": True,
        "forbidden_seed_terms_detected": bool(occurrences),
        "forbidden_seed_terms_count": len(occurrences),
        "forbidden_seed_term_occurrences": occurrences,
        "target_like_fields_detected": bool(matched_terms & TARGET_LIKE_TERMS),
        "future_information_fields_detected": bool(matched_terms & FUTURE_LIKE_TERMS),
        "label_like_fields_detected": bool(matched_terms & LABEL_LIKE_TERMS),
        "prediction_like_fields_detected": bool(matched_terms & PREDICTION_LIKE_TERMS),
    }


def _scan_node(value: Any, *, file: str, json_path: str, occurrences: list[dict[str, str]]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _scan_text(
                str(key),
                file=file,
                json_path=f"{json_path}.{key}",
                occurrences=occurrences,
            )
            _scan_node(item, file=file, json_path=f"{json_path}.{key}", occurrences=occurrences)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_node(item, file=file, json_path=f"{json_path}[{index}]", occurrences=occurrences)
    elif isinstance(value, str):
        _scan_text(value, file=file, json_path=json_path, occurrences=occurrences)


def _scan_text(text: str, *, file: str, json_path: str, occurrences: list[dict[str, str]]) -> None:
    matched = _matched_terms(text)
    for term in matched:
        occurrences.append(
            {
                "file": file,
                "json_path": json_path,
                "offending_key_or_value": text,
                "matched_term": term,
            }
        )


def _matched_terms(text: str) -> list[str]:
    tokens = _tokens(text)
    compact = "".join(tokens)
    token_set = set(tokens)
    matches: list[str] = []
    for term in FORBIDDEN_SEED_FIELD_TERMS:
        term_tokens = _tokens(term)
        term_compact = "".join(term_tokens)
        if term == "ev":
            if "ev" in token_set:
                matches.append(term)
            continue
        if len(term_tokens) == 1:
            term_token = term_tokens[0]
            if term_token in token_set or term_token in compact:
                matches.append(term)
        elif term_compact in compact:
            matches.append(term)
    return sorted(set(matches))


def _tokens(text: str) -> list[str]:
    camel_split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return [token for token in re.split(r"[^A-Za-z0-9]+", camel_split.lower()) if token]
