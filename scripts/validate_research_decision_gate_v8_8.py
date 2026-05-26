from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.validation.safety import validate_exact_keys, validate_markdown_forbidden_claims


VERSION = "V8.8"
DECISION_JSON = Path("reports/research_decisions/v8_8_research_decision_gate.json")
DECISION_MD = Path("reports/research_decisions/v8_8_research_decision_gate.md")
DOC_MD = Path("docs/research_decision_gate_v8_8.md")
REQUIRED_TOP_LEVEL_KEYS = {
    "version",
    "status",
    "decision_gate_type",
    "created_at_utc",
    "inputs",
    "summary_verdict",
    "walk_forward_assessment",
    "baseline_assessment",
    "fold_stability_assessment",
    "timeframe_stability_assessment",
    "label_shuffle_assessment",
    "static_split_comparison_assessment",
    "leakage_assessment",
    "limitations",
    "recommended_next_step",
    "secondary_next_step",
    "roadmap",
    "safety",
    "claims",
}
EXPECTED_SAFETY = {
    "trading_enabled": False,
    "paper_live_enabled": False,
    "orders_enabled": False,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
}
EXPECTED_CLAIMS = {
    "strategy_validated": False,
    "model_validated_for_trading": False,
    "walk_forward_validated_for_trading": False,
    "profitability_claimed": False,
    "real_trading_allowed": False,
}
FORBIDDEN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "validated trading strategy",
    "model validated for trading",
    "walk-forward validated for trading",
    "walk forward validated for trading",
]
FORBIDDEN_ARTIFACT_ROOTS = [
    Path("reports/backtests"),
    Path("reports/strategies"),
    Path("orders"),
    Path("execution"),
    Path("models"),
    Path("checkpoints"),
    Path("data/research/v8_8/backtests"),
    Path("data/research/v8_8/strategies"),
    Path("data/research/v8_8/orders"),
    Path("data/research/v8_8/execution"),
    Path("data/research/v8_8/models"),
]
IGNORED_SCAN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
PERSISTENT_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def main() -> None:
    result = validate_research_decision_gate_v8_8(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


def validate_research_decision_gate_v8_8(project_root: Path = Path(".")) -> dict[str, Any]:
    root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    report_path = root / DECISION_JSON
    markdown_path = root / DECISION_MD
    doc_path = root / DOC_MD
    if not report_path.exists():
        return _result([f"missing V8.8 decision JSON report: {DECISION_JSON}"], warnings)
    if not markdown_path.exists():
        errors.append(f"missing V8.8 decision Markdown report: {DECISION_MD}")
    if not doc_path.exists():
        errors.append(f"missing V8.8 decision documentation: {DOC_MD}")
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _result([f"invalid V8.8 decision JSON report: {exc}"], warnings)
    errors.extend(validate_research_decision_payload_v8_8(payload))
    for path, label in [(markdown_path, "V8.8 decision Markdown report"), (doc_path, "V8.8 decision documentation")]:
        if path.exists():
            errors.extend(validate_research_decision_markdown_text_v8_8(path.read_text(encoding="utf-8"), label))
    errors.extend(find_forbidden_v8_8_artifacts(root))
    return _result(errors, warnings, payload)


def validate_research_decision_payload_v8_8(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(payload, REQUIRED_TOP_LEVEL_KEYS, "V8.8 decision report"))
    if payload.get("version") != VERSION:
        errors.append("V8.8 decision report version mismatch")
    if payload.get("status") != "PASS":
        errors.append("V8.8 decision report status must be PASS")
    if payload.get("decision_gate_type") != "research_only":
        errors.append("V8.8 decision_gate_type must be research_only")
    for key in [
        "walk_forward_assessment",
        "baseline_assessment",
        "fold_stability_assessment",
        "timeframe_stability_assessment",
        "label_shuffle_assessment",
        "static_split_comparison_assessment",
        "leakage_assessment",
    ]:
        if not isinstance(payload.get(key), dict) or not payload[key]:
            errors.append(f"V8.8 {key} must be present")
    if not str(payload.get("recommended_next_step", "")).strip():
        errors.append("V8.8 recommended_next_step must be non-empty")
    if not str(payload.get("secondary_next_step", "")).strip():
        errors.append("V8.8 secondary_next_step must be non-empty")
    if payload.get("recommended_next_step", "").startswith("E."):
        errors.append("V8.8 must not recommend a backtest as primary next step")
    if not isinstance(payload.get("roadmap"), list) or not payload["roadmap"]:
        errors.append("V8.8 roadmap must be non-empty")
    if not isinstance(payload.get("limitations"), list) or not payload["limitations"]:
        errors.append("V8.8 limitations must be non-empty")
    if payload.get("safety") != EXPECTED_SAFETY:
        errors.append("V8.8 decision safety flags mismatch")
    if payload.get("claims") != EXPECTED_CLAIMS:
        errors.append("V8.8 decision claims mismatch")
    label_shuffle = payload.get("label_shuffle_assessment", {})
    if label_shuffle.get("no_clear_edge_vs_shuffled_labels_count", 0) <= 0:
        errors.append("V8.8 label shuffle assessment must preserve no-clear-edge warning cases")
    if label_shuffle.get("falsification_clean") is not False:
        errors.append("V8.8 label shuffle assessment must mark falsification_clean false")
    if payload.get("walk_forward_assessment", {}).get("not_a_backtest") is not True:
        errors.append("V8.8 walk_forward_assessment must mark not_a_backtest true")
    if payload.get("baseline_assessment", {}).get("backtest_recommended") is not False:
        errors.append("V8.8 baseline assessment must not recommend backtest")
    return errors


def validate_research_decision_markdown_text_v8_8(text: str, label: str) -> list[str]:
    errors = validate_markdown_forbidden_claims(text, label)
    lowered = text.casefold()
    errors.extend(f"{label} contains forbidden claim: {claim}" for claim in FORBIDDEN_CLAIMS if claim in lowered)
    for required in [
        "V8.7 est une validation walk-forward offline stricte, pas un backtest",
        "Un backtest research n'est pas justifie maintenant",
        "Pas de trading",
        "Pas de paper live",
        "Pas d'ordre",
    ]:
        if required.casefold() not in lowered:
            errors.append(f"{label} missing required statement: {required}")
    return errors


def find_forbidden_v8_8_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_ARTIFACT_ROOTS:
        if (root / relative).exists():
            errors.append(f"Forbidden V8.8 artifact detected: {relative}")
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_SCAN_PARTS for part in path.parts):
            continue
        if path.suffix.casefold() in PERSISTENT_MODEL_SUFFIXES:
            errors.append(f"Forbidden V8.8 persistent model artifact detected: {path.relative_to(root)}")
    return errors


def _result(errors: list[str], warnings: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION, "passed": not errors, "errors": errors, "warnings": warnings, "report": report}


if __name__ == "__main__":
    main()
