from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import _bootstrap

_bootstrap.bootstrap_src_path()


VERSION = "V8.1"
REPORT_JSON = Path("reports/research_decisions/v8_1_research_decision_gate.json")
REPORT_MD = Path("reports/research_decisions/v8_1_research_decision_gate.md")
DOC_MD = Path("docs/research_decision_gate_v8_1.md")
FORBIDDEN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "validated trading strategy",
    "ohlcv trades validated for trading",
    "ohlcv + trades validated for trading",
]
FORBIDDEN_ARTIFACT_PATHS = [
    Path("reports/backtests"),
    Path("reports/strategies"),
    Path("orders"),
    Path("execution"),
    Path("models"),
    Path("data/research/v8_1/backtests"),
    Path("data/research/v8_1/strategies"),
    Path("data/research/v8_1/orders"),
    Path("data/research/v8_1/execution"),
    Path("data/research/v8_1/models"),
]
PERSISTENT_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
REQUIRED_TOP_LEVEL_KEYS = {
    "version",
    "status",
    "decision_gate_type",
    "created_at_utc",
    "inputs",
    "summary_verdict",
    "ohlcv_trades_90d_assessment",
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


def main() -> None:
    result = validate_research_decision_gate_v8_1(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


def validate_research_decision_gate_v8_1(project_root: Path = Path(".")) -> dict[str, Any]:
    root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    report_path = root / REPORT_JSON
    markdown_path = root / REPORT_MD
    doc_path = root / DOC_MD
    if not report_path.exists():
        return _result([f"missing V8.1 JSON report: {REPORT_JSON}"], warnings)
    if not markdown_path.exists():
        errors.append(f"missing V8.1 Markdown report: {REPORT_MD}")
    if not doc_path.exists():
        errors.append(f"missing V8.1 documentation: {DOC_MD}")

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _result([f"invalid V8.1 JSON report: {exc}"], warnings)

    errors.extend(validate_research_decision_payload_v8_1(report))
    errors.extend(_validate_markdown_claims(markdown_path, "V8.1 Markdown report"))
    errors.extend(_validate_markdown_claims(doc_path, "V8.1 documentation"))
    errors.extend(_find_forbidden_artifacts(root))
    return _result(errors, warnings, report)


def validate_research_decision_payload_v8_1(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(_validate_exact_keys(payload, REQUIRED_TOP_LEVEL_KEYS, "V8.1 report"))
    if payload.get("version") != VERSION:
        errors.append("V8.1 version mismatch")
    if payload.get("status") != "PASS":
        errors.append("V8.1 status must be PASS")
    if payload.get("decision_gate_type") != "research_only":
        errors.append("V8.1 decision_gate_type must be research_only")
    if not isinstance(payload.get("ohlcv_trades_90d_assessment"), dict) or not payload["ohlcv_trades_90d_assessment"]:
        errors.append("V8.1 ohlcv_trades_90d_assessment must be present")
    if not isinstance(payload.get("comparison_to_references_assessment"), dict):
        errors.append("V8.1 comparison_to_references_assessment must be present")
    if not str(payload.get("recommended_next_step", "")).strip():
        errors.append("V8.1 recommended_next_step must be non-empty")
    if not str(payload.get("secondary_next_step", "")).strip():
        errors.append("V8.1 secondary_next_step must be non-empty")
    roadmap = payload.get("roadmap")
    if not isinstance(roadmap, list) or not roadmap:
        errors.append("V8.1 roadmap must be non-empty")
    safety = payload.get("safety", {})
    if not isinstance(safety, dict):
        errors.append("V8.1 safety must be an object")
    else:
        for key in ["trading_enabled", "paper_live_enabled", "orders_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled"]:
            if safety.get(key) is not False:
                errors.append(f"V8.1 safety flag must be false: {key}")
    claims = payload.get("claims", {})
    if not isinstance(claims, dict):
        errors.append("V8.1 claims must be an object")
    else:
        for key in [
            "strategy_validated",
            "model_validated_for_trading",
            "ohlcv_trades_validated_for_trading",
            "profitability_claimed",
            "real_trading_allowed",
        ]:
            if claims.get(key) is not False:
                errors.append(f"V8.1 claim flag must be false: {key}")
    limitations = payload.get("limitations")
    if not isinstance(limitations, list) or not limitations:
        errors.append("V8.1 limitations must be non-empty")
    return errors


def _validate_markdown_claims(path: Path, label: str) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").casefold()
    return [f"{label} contains forbidden claim: {claim}" for claim in FORBIDDEN_CLAIMS if claim in text]


def _find_forbidden_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_ARTIFACT_PATHS:
        path = root / relative
        if path.exists():
            errors.append(f"Forbidden V8.1 artifact detected: {relative.as_posix()}")
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    errors.append(f"Forbidden V8.1 artifact detected: {child.relative_to(root).as_posix()}")
    for path in root.rglob("*"):
        if ".git" in path.parts or ".venv" in path.parts or not path.is_file():
            continue
        if path.suffix.casefold() in PERSISTENT_MODEL_SUFFIXES:
            errors.append(f"Forbidden persistent model artifact detected: {path.relative_to(root).as_posix()}")
    return sorted(set(errors))


def _validate_exact_keys(payload: Any, expected: set[str], label: str) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label} must be an object"]
    actual = set(payload)
    errors: list[str] = []
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        errors.append(f"{label} missing keys: {missing}")
    if unexpected:
        errors.append(f"{label} unexpected keys: {unexpected}")
    return errors


def _result(errors: list[str], warnings: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"passed": not errors, "errors": errors, "warnings": warnings, "report": report}


if __name__ == "__main__":
    main()
