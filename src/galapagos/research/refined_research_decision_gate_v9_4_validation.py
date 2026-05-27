from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.refined_research_decision_gate_v9_4 import (
    ALLOWED_RESEARCH_DECISIONS,
    DOC_MD_PATH,
    FINDINGS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY,
    VERSION,
)
from galapagos.validation.safety import validate_exact_keys


REQUIRED_DECISION_KEYS = {
    "version",
    "status",
    "decision_gate_type",
    "created_at_utc",
    "inputs",
    "window",
    "source_versions",
    "target_name",
    "models",
    "timeframes",
    "feature_columns_count",
    "selected_features_count",
    "v9_2_static_split_assessment",
    "v9_3_walk_forward_assessment",
    "baseline_assessment",
    "fold_stability_assessment",
    "timeframe_stability_assessment",
    "label_shuffle_assessment",
    "static_split_vs_walk_forward_assessment",
    "feature_leakage_scan",
    "metric_forbidden_scan",
    "selected_features_coherence",
    "forbidden_claims_assessment",
    "research_decision",
    "decision_justification",
    "evidence_used",
    "warnings",
    "confidence_level",
    "next_step_recommendation",
    "secondary_next_step_recommendation",
    "explicit_no_trading_statement",
    "findings",
    "safety",
    "limitations",
}

REQUIRED_MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "decision_gate_type",
    "research_decision",
    "input_reports",
    "window",
    "feature_columns_count",
    "selected_features_count",
    "outputs",
    "baseline_assessment",
    "fold_stability_assessment",
    "timeframe_stability_assessment",
    "label_shuffle_assessment",
    "static_split_vs_walk_forward_assessment",
    "feature_leakage_scan",
    "metric_forbidden_scan",
    "selected_features_coherence",
    "findings",
    "safety",
    "limitations",
}

FORBIDDEN_MARKDOWN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "model validated for trading",
    "walk-forward validated for trading",
    "walk forward validated for trading",
    "profitability confirmed",
]

FORBIDDEN_V9_4_ARTIFACT_ROOTS = [
    Path("reports/backtests"),
    Path("reports/strategies"),
    Path("orders"),
    Path("execution"),
    Path("models"),
    Path("checkpoints"),
    Path("data/research/v9_4/backtests"),
    Path("data/research/v9_4/strategies"),
    Path("data/research/v9_4/orders"),
    Path("data/research/v9_4/execution"),
    Path("data/research/v9_4/models"),
]

PERSISTENT_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt"}
IGNORED_SCAN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}


def validate_refined_research_decision_gate_v9_4(project_root: Path = Path(".")) -> dict[str, Any]:
    root = project_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    decision_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    doc_path = root / DOC_MD_PATH
    for path, label in [
        (decision_path, "V9.4 decision JSON"),
        (manifest_path, "V9.4 manifest"),
        (markdown_path, "V9.4 Markdown report"),
        (doc_path, "V9.4 documentation"),
    ]:
        if not path.exists():
            errors.append(f"missing {label}: {path.relative_to(root)}")
    if errors:
        return _result(errors, warnings)
    decision = _read_json(decision_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_decision_payload_v9_4(decision))
    errors.extend(validate_manifest_payload_v9_4(manifest, decision))
    errors.extend(validate_markdown_text_v9_4(markdown_path.read_text(encoding="utf-8"), "V9.4 Markdown report"))
    errors.extend(validate_markdown_text_v9_4(doc_path.read_text(encoding="utf-8"), "V9.4 documentation"))
    errors.extend(find_forbidden_v9_4_artifacts(root))
    return _result(errors, warnings, decision, manifest)


def validate_decision_payload_v9_4(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(payload, REQUIRED_DECISION_KEYS, "V9.4 decision report"))
    if payload.get("version") != VERSION:
        errors.append("V9.4 decision report version mismatch")
    if payload.get("status") != "PASS":
        errors.append("V9.4 decision report status must be PASS")
    if payload.get("decision_gate_type") != "research_only":
        errors.append("V9.4 decision_gate_type must be research_only")
    if payload.get("research_decision") not in ALLOWED_RESEARCH_DECISIONS:
        errors.append("V9.4 research_decision is not allowed")
    if payload.get("research_decision") == "limited_research_backtest_candidate":
        errors.append("V9.4 must not authorize a limited research backtest with current evidence")
    if payload.get("findings") != FINDINGS:
        errors.append("V9.4 findings flags mismatch")
    if payload.get("safety") != SAFETY:
        errors.append("V9.4 safety flags mismatch")
    if payload.get("feature_leakage_scan", {}).get("passed") is not True:
        errors.append("V9.4 feature leakage scan must pass")
    if payload.get("metric_forbidden_scan", {}).get("passed") is not True:
        errors.append("V9.4 metric forbidden scan must pass")
    if payload.get("selected_features_coherence", {}).get("passed") is not True:
        errors.append("V9.4 selected features coherence must pass")
    label_shuffle = payload.get("label_shuffle_assessment", {})
    if label_shuffle.get("no_clear_edge_vs_shuffled_labels_count", 0) <= 0:
        errors.append("V9.4 must preserve no-clear-edge vs shuffled labels warnings")
    if label_shuffle.get("falsification_clean") is not False:
        errors.append("V9.4 label shuffle falsification must not be marked clean")
    if payload.get("baseline_assessment", {}).get("backtest_not_justified") is not True:
        errors.append("V9.4 baseline assessment must reject backtest")
    if not payload.get("warnings"):
        errors.append("V9.4 warnings must be non-empty")
    statement = str(payload.get("explicit_no_trading_statement", "")).casefold()
    for required in ["aucun trading", "aucun paper live", "aucun ordre", "aucun signal actionnable"]:
        if required not in statement:
            errors.append(f"V9.4 explicit_no_trading_statement missing: {required}")
    return errors


def validate_manifest_payload_v9_4(manifest: dict[str, Any], decision: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, REQUIRED_MANIFEST_KEYS, "V9.4 manifest"))
    if manifest.get("version") != VERSION:
        errors.append("V9.4 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V9.4 manifest status must be PASS")
    if manifest.get("decision_gate_type") != "research_only":
        errors.append("V9.4 manifest decision_gate_type mismatch")
    if manifest.get("research_decision") != decision.get("research_decision"):
        errors.append("V9.4 manifest research_decision mismatch")
    if manifest.get("findings") != FINDINGS:
        errors.append("V9.4 manifest findings mismatch")
    if manifest.get("safety") != SAFETY:
        errors.append("V9.4 manifest safety mismatch")
    return errors


def validate_markdown_text_v9_4(text: str, label: str) -> list[str]:
    errors: list[str] = []
    lowered = text.casefold()
    for claim in FORBIDDEN_MARKDOWN_CLAIMS:
        if claim in lowered:
            errors.append(f"{label} contains forbidden claim: {claim}")
    for required in [
        "Decision research",
        "aucun backtest",
        "aucun signal actionnable",
        "aucun ordre",
        "aucun trading reel",
    ]:
        if required.casefold() not in lowered:
            errors.append(f"{label} missing required statement: {required}")
    return errors


def find_forbidden_v9_4_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in FORBIDDEN_V9_4_ARTIFACT_ROOTS:
        if (root / relative).exists():
            errors.append(f"Forbidden V9.4 artifact detected: {relative}")
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_SCAN_PARTS for part in path.parts):
            continue
        if path.suffix.casefold() in PERSISTENT_MODEL_SUFFIXES:
            errors.append(f"Forbidden persistent model artifact detected: {path.relative_to(root)}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(
    errors: list[str],
    warnings: list[str],
    decision: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {"version": VERSION, "passed": not errors, "errors": errors, "warnings": warnings, "report": decision, "manifest": manifest}
