from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.ohlcv_trades_1y_robustness import (
    DECISION_GATE_CLAIMS_V8_6,
    DECISION_GATE_DOC_PATH_V8_6,
    DECISION_GATE_JSON_PATH_V8_6,
    DECISION_GATE_MD_PATH_V8_6,
    DECISION_GATE_SAFETY_V8_6,
    VERSION_V8_6,
)
from galapagos.ml.ohlcv_trades_1y_robustness_validation import _find_forbidden_v8_6_artifacts
from galapagos.validation.safety import validate_exact_keys, validate_markdown_forbidden_claims


REQUIRED_TOP_LEVEL_KEYS = {
    "version",
    "status",
    "decision_gate_type",
    "created_at_utc",
    "inputs",
    "summary_verdict",
    "ohlcv_trades_1y_assessment",
    "comparison_to_references_assessment",
    "baseline_assessment",
    "split_stability_assessment",
    "timeframe_stability_assessment",
    "walk_forward_stability_assessment",
    "label_shuffle_assessment",
    "leakage_assessment",
    "limitations",
    "recommended_next_step",
    "secondary_next_step",
    "roadmap",
    "safety",
    "claims",
}
FORBIDDEN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "validated trading strategy",
    "model validated for trading",
    "ohlcv trades validated for trading",
    "ohlcv + trades validated for trading",
]


def main() -> None:
    result = validate_research_decision_gate_v8_6(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


def validate_research_decision_gate_v8_6(project_root: Path = Path(".")) -> dict[str, Any]:
    root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    report_path = root / DECISION_GATE_JSON_PATH_V8_6
    markdown_path = root / DECISION_GATE_MD_PATH_V8_6
    doc_path = root / DECISION_GATE_DOC_PATH_V8_6
    if not report_path.exists():
        return _result([f"missing V8.6 decision JSON report: {DECISION_GATE_JSON_PATH_V8_6}"], warnings)
    if not markdown_path.exists():
        errors.append(f"missing V8.6 decision Markdown report: {DECISION_GATE_MD_PATH_V8_6}")
    if not doc_path.exists():
        errors.append(f"missing V8.6 decision documentation: {DECISION_GATE_DOC_PATH_V8_6}")

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _result([f"invalid V8.6 decision JSON report: {exc}"], warnings)

    errors.extend(validate_research_decision_payload_v8_6(report))
    errors.extend(_validate_markdown(markdown_path, "V8.6 decision Markdown report"))
    errors.extend(_validate_markdown(doc_path, "V8.6 decision documentation"))
    errors.extend(_find_forbidden_v8_6_artifacts(root))
    return _result(errors, warnings, report)


def validate_research_decision_payload_v8_6(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(payload, REQUIRED_TOP_LEVEL_KEYS, "V8.6 decision report"))
    if payload.get("version") != VERSION_V8_6:
        errors.append("V8.6 decision report version mismatch")
    if payload.get("status") != "PASS":
        errors.append("V8.6 decision report status must be PASS")
    if payload.get("decision_gate_type") != "research_only":
        errors.append("V8.6 decision_gate_type must be research_only")
    for key in [
        "ohlcv_trades_1y_assessment",
        "comparison_to_references_assessment",
        "baseline_assessment",
        "split_stability_assessment",
        "timeframe_stability_assessment",
        "walk_forward_stability_assessment",
        "label_shuffle_assessment",
        "leakage_assessment",
    ]:
        if not isinstance(payload.get(key), dict) or not payload[key]:
            errors.append(f"V8.6 {key} must be present")
    if not str(payload.get("recommended_next_step", "")).strip():
        errors.append("V8.6 recommended_next_step must be non-empty")
    if not str(payload.get("secondary_next_step", "")).strip():
        errors.append("V8.6 secondary_next_step must be non-empty")
    if not isinstance(payload.get("roadmap"), list) or not payload["roadmap"]:
        errors.append("V8.6 roadmap must be non-empty")
    if not isinstance(payload.get("limitations"), list) or not payload["limitations"]:
        errors.append("V8.6 limitations must be non-empty")
    if payload.get("safety") != DECISION_GATE_SAFETY_V8_6:
        errors.append("V8.6 decision safety flags mismatch")
    if payload.get("claims") != DECISION_GATE_CLAIMS_V8_6:
        errors.append("V8.6 decision claims mismatch")
    return errors


def _validate_markdown(path: Path, label: str) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    errors = validate_markdown_forbidden_claims(text, label)
    lowered = text.casefold()
    errors.extend(f"{label} contains forbidden claim: {claim}" for claim in FORBIDDEN_CLAIMS if claim in lowered)
    return errors


def _result(errors: list[str], warnings: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION_V8_6, "passed": not errors, "errors": errors, "warnings": warnings, "report": report}


if __name__ == "__main__":
    main()
