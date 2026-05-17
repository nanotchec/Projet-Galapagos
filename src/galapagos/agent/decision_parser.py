from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from galapagos.agent.decision_schema import AgentDecision, no_trade_decision


@dataclass(frozen=True)
class DecisionParseResult:
    decision: AgentDecision
    validity: str
    error: str | None = None
    extracted_json: str | None = None
    parser_repair_applied: bool = False
    raw_json_valid: bool = False
    enum_violations: list[dict[str, Any]] | None = None


def parse_decision_response(
    raw_response: str,
    profile: str,
    asset: str,
    horizon: str,
) -> AgentDecision:
    return parse_decision_response_with_metadata(raw_response, profile, asset, horizon).decision


def parse_decision_response_with_metadata(
    raw_response: str,
    profile: str,
    asset: str,
    horizon: str,
) -> DecisionParseResult:
    try:
        extracted = extract_json_object(raw_response)
        payload = json.loads(extracted)
        decision = AgentDecision.model_validate(payload)
        raw_json_valid = raw_response.strip() == extracted
        return DecisionParseResult(
            decision=decision,
            validity="valid_schema",
            extracted_json=extracted,
            parser_repair_applied=not raw_json_valid,
            raw_json_valid=raw_json_valid,
        )
    except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as original_exc:
        exc: Exception = original_exc
        enum_violations = _enum_violations_from_error(original_exc)
        repaired = attempt_json_repair(raw_response)
        if repaired is not None:
            try:
                payload = json.loads(repaired)
                decision = AgentDecision.model_validate(payload)
                return DecisionParseResult(
                    decision=decision,
                    validity="repaired_json",
                    extracted_json=repaired,
                    parser_repair_applied=True,
                    raw_json_valid=False,
                )
            except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as repair_exc:
                exc = repair_exc
                enum_violations = _enum_violations_from_error(repair_exc)
        return DecisionParseResult(
            decision=no_trade_decision(profile, asset, horizon, f"Invalid LLM decision: {exc}"),
            validity="parser_fallback",
            error=str(exc),
            raw_json_valid=False,
            enum_violations=enum_violations,
        )


def attempt_json_repair(raw_response: str) -> str | None:
    try:
        candidate = extract_json_object(raw_response)
        json.loads(candidate)
    except (json.JSONDecodeError, ValueError, TypeError):
        return None
    return candidate.strip()


def extract_json_object(raw_response: str) -> str:
    text = raw_response.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object found in LLM response")
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(text[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise ValueError("Unclosed JSON object in LLM response")


def _enum_violations_from_error(error: Exception) -> list[dict[str, Any]]:
    if not isinstance(error, ValidationError):
        return []
    violations: list[dict[str, Any]] = []
    for item in error.errors():
        field = ".".join(str(part) for part in item.get("loc", ()))
        error_type = str(item.get("type") or "")
        if error_type not in {"enum", "literal_error", "string_pattern_mismatch"}:
            continue
        violations.append(
            {
                "field_name": field,
                "invalid_value": item.get("input"),
                "allowed_values": _allowed_values_for_field(field),
            }
        )
    return violations


def _allowed_values_for_field(field_name: str) -> list[str]:
    if field_name == "decision":
        return ["LONG", "SHORT", "CLOSE", "HOLD", "NO_TRADE"]
    if field_name == "strategy":
        return [
            "no_trade",
            "breakout",
            "momentum",
            "mean_reversion",
            "derivatives_signal",
            "volatility_regime",
            "risk_reduction",
            "close_position",
        ]
    if field_name == "setup_quality":
        return ["poor", "acceptable", "good", "excellent"]
    return []
