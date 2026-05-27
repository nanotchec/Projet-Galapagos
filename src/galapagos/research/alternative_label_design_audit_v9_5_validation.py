from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.alternative_label_design_audit_v9_5 import (
    ALLOWED_DECISIONS,
    FINDINGS,
    FORBIDDEN_OUTPUT_TERMS,
    LAST_VALIDATED_VERSION,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY,
    VERSION,
)


FORBIDDEN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "profitability confirmed",
]


def validate_alternative_label_design_audit_v9_5(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.exists():
        errors.append(f"missing report JSON: {REPORT_JSON_PATH}")
        return errors
    if not manifest_path.exists():
        errors.append(f"missing manifest JSON: {MANIFEST_PATH}")
        return errors
    if not markdown_path.exists():
        errors.append(f"missing report Markdown: {REPORT_MD_PATH}")
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_5(report))
    errors.extend(validate_manifest_payload_v9_5(manifest, report))
    errors.extend(validate_markdown_text_v9_5(markdown_path.read_text(encoding="utf-8"), REPORT_MD_PATH.as_posix()))
    errors.extend(validate_no_forbidden_artifacts_v9_5(root))
    return errors


def validate_report_payload_v9_5(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.5 report version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.5 report status must be PASS")
    if report.get("decision_type") != "alternative_label_design_audit":
        errors.append("V9.5 decision_type mismatch")
    source = report.get("source_decision", {})
    if source.get("research_decision") != "backtest_not_justified_refine_labels":
        errors.append("V9.5 must preserve the V9.4 conservative decision")
    current = report.get("current_label_analysis", {})
    if current.get("target_name") != "up_down_flat_h1":
        errors.append("V9.5 target_name must be up_down_flat_h1")
    if not current.get("timeframes"):
        errors.append("V9.5 current label analysis must contain timeframes")
    for timeframe, payload in current.get("timeframes", {}).items():
        if payload.get("class_distribution") is None:
            errors.append(f"V9.5 missing class distribution for {timeframe}")
        if "majority_rate" not in payload:
            errors.append(f"V9.5 missing majority_rate for {timeframe}")
    diagnostic = report.get("problem_diagnostic", {})
    for key in [
        "labels_too_noisy",
        "thresholds_likely_too_weak_or_not_scaled",
        "class_imbalance_present",
        "flat_class_definition_issue",
        "no_clear_edge_vs_shuffled_labels_count",
    ]:
        if key not in diagnostic:
            errors.append(f"V9.5 missing diagnostic key: {key}")
    if diagnostic.get("no_clear_edge_vs_shuffled_labels_count", 0) <= 0:
        errors.append("V9.5 must preserve the label-shuffle no-clear-edge evidence")
    catalog = report.get("alternative_label_design_catalog", [])
    if not catalog:
        errors.append("V9.5 alternative label design catalog must be non-empty")
    family_ids = {item.get("family_id") for item in catalog}
    for required in {"fixed_stricter_thresholds", "volatility_normalized_thresholds", "rolling_quantile_or_tertile_labels", "causal_multi_horizon_labels"}:
        if required not in family_ids:
            errors.append(f"V9.5 missing label design family: {required}")
    decision = report.get("v9_5_decision", {})
    if decision.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.5 decision is not allowed")
    if decision.get("decision") == "limited_research_backtest_candidate":
        errors.append("V9.5 must never recommend a backtest candidate")
    if decision.get("next_step") != "V9.6 - Refined Label Factory Candidate":
        errors.append("V9.5 next step must be V9.6 label factory candidate")
    if report.get("findings") != FINDINGS:
        errors.append("V9.5 findings flags mismatch")
    safety = report.get("safety", {})
    for key, expected in SAFETY.items():
        if safety.get(key) is not expected:
            errors.append(f"V9.5 safety flag mismatch: {key}")
    if report.get("leakage_guard", {}).get("passed") is not True:
        errors.append("V9.5 leakage guard must pass")
    if report.get("forbidden_output_scan", {}).get("passed") is not True:
        errors.append("V9.5 forbidden output scan must pass")
    errors.extend(_scan_for_forbidden_metric_keys(report))
    return errors


def validate_manifest_payload_v9_5(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.5 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V9.5 manifest status must be PASS")
    if manifest.get("decision_type") != "alternative_label_design_audit":
        errors.append("V9.5 manifest decision_type mismatch")
    if manifest.get("v9_5_decision", {}).get("decision") != report.get("v9_5_decision", {}).get("decision"):
        errors.append("V9.5 manifest decision mismatch")
    if manifest.get("source_decision", {}).get("research_decision") != report.get("source_decision", {}).get("research_decision"):
        errors.append("V9.5 manifest source decision mismatch")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.5 manifest findings mismatch")
    if manifest.get("safety") != report.get("safety"):
        errors.append("V9.5 manifest safety mismatch")
    return errors


def validate_markdown_text_v9_5(text: str, label: str) -> list[str]:
    lowered = text.casefold()
    errors = []
    for forbidden in FORBIDDEN_CLAIMS:
        if forbidden in lowered:
            errors.append(f"{label} contains forbidden claim: {forbidden}")
    required = [
        "aucun backtest",
        "aucune strategie",
        "aucun signal actionnable",
        "aucun ordre",
        "aucun trading reel",
    ]
    for phrase in required:
        if phrase not in lowered:
            errors.append(f"{label} missing required safety phrase: {phrase}")
    return errors


def validate_no_forbidden_artifacts_v9_5(root: Path) -> list[str]:
    errors: list[str] = []
    forbidden_paths = [
        root / "data/research/v9_5",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models/model.pkl",
    ]
    for path in forbidden_paths:
        if path.exists():
            errors.append(f"forbidden V9.5 artifact exists: {path}")
    for pattern in ["*.pkl", "*.pickle", "*.joblib", "*.onnx", "*.pt", "*.pth", "*.ckpt"]:
        matches = [path for path in root.glob(pattern) if path.is_file()]
        if matches:
            errors.append(f"forbidden persistent model files present: {[str(path) for path in matches]}")
    return errors


def _scan_for_forbidden_metric_keys(payload: Any) -> list[str]:
    errors: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key).casefold()
                if key_text in FORBIDDEN_OUTPUT_TERMS:
                    errors.append(f"forbidden output key present at {path}.{key}")
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(payload, "report")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
