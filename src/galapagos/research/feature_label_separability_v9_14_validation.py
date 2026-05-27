from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.feature_label_separability_v9_14 import (
    ALLOWED_DECISIONS,
    DECISION_TYPE,
    FINDINGS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY,
    SAFETY_FLAGS,
    TARGET_NAME_V9_13,
    VERSION,
)


FORBIDDEN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "profitability confirmed",
]
FORBIDDEN_TERMS = ["pnl", "sharpe", "drawdown", "equity curve", "profit factor"]
FORBIDDEN_FILENAMES = {"Icon", "Icon\r", ".DS_Store", ".env"}
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key", ".sha256.json", ".sha256.txt"}


def validate_feature_label_separability_v9_14(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.exists():
        errors.append(f"missing V9.14 report: {REPORT_JSON_PATH}")
        return errors
    if not manifest_path.exists():
        errors.append(f"missing V9.14 manifest: {MANIFEST_PATH}")
        return errors
    if not markdown_path.exists():
        errors.append(f"missing V9.14 markdown: {REPORT_MD_PATH}")
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_14(report))
    errors.extend(validate_manifest_payload_v9_14(manifest, report))
    errors.extend(validate_markdown_v9_14(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_14(root))
    return errors


def validate_report_payload_v9_14(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.14 report version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.14 status must be PASS")
    if report.get("decision_type") != DECISION_TYPE:
        errors.append("V9.14 decision_type mismatch")
    if report.get("target_name") != TARGET_NAME_V9_13:
        errors.append("V9.14 target mismatch")
    decision = report.get("v9_14_decision", {})
    if decision.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.14 decision is not allowed")
    if "backtest" in str(decision.get("decision", "")).casefold():
        errors.append("V9.14 decision must not recommend a backtest")
    label_diag = report.get("label_diagnostic_v9_13", {})
    if "1m" not in label_diag.get("timeframes", {}) or "1h" not in label_diag.get("timeframes", {}):
        errors.append("V9.14 label diagnostic must include 1m and 1h")
    ml_diag = report.get("ml_diagnostic_v9_13", {})
    if ml_diag.get("learned_vs_baselines", {}).get("clear_wins_count") != 0:
        errors.append("V9.14 must preserve V9.13 zero clear wins")
    if ml_diag.get("learned_vs_shuffled_labels", {}).get("no_clear_edge_vs_shuffled_labels_count") != 14:
        errors.append("V9.14 must preserve V9.13 no-clear shuffle count")
    if ml_diag.get("walk_forward_not_repeated_in_v9_14") is not True:
        errors.append("V9.14 must not repeat walk-forward")
    separability = report.get("feature_label_separability", {})
    if separability.get("model_training_performed") is not False:
        errors.append("V9.14 separability must not train a model")
    if separability.get("signal_produced") is not False:
        errors.append("V9.14 separability must not produce a signal")
    if not separability.get("by_timeframe"):
        errors.append("V9.14 separability must contain timeframe diagnostics")
    hypotheses = report.get("hypotheses", [])
    if {item.get("id") for item in hypotheses} != {"H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"}:
        errors.append("V9.14 hypotheses H1-H8 must be complete")
    if report.get("forbidden_metric_scan", {}).get("passed") is not True:
        errors.append("V9.14 forbidden metric scan must pass")
    if report.get("findings") != FINDINGS:
        errors.append("V9.14 findings mismatch")
    for key, expected in SAFETY.items():
        if report.get("safety", {}).get(key) is not expected:
            errors.append(f"V9.14 safety mismatch: {key}")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"V9.14 safety flag mismatch: {key}")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.14 report must not contain sidecar or ZIP hash fields")
    return errors


def validate_manifest_payload_v9_14(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.14 manifest version mismatch")
    if manifest.get("status") != report.get("status"):
        errors.append("V9.14 manifest status mismatch")
    if manifest.get("decision_type") != DECISION_TYPE:
        errors.append("V9.14 manifest decision_type mismatch")
    if manifest.get("v9_14_decision", {}).get("decision") != report.get("v9_14_decision", {}).get("decision"):
        errors.append("V9.14 manifest decision mismatch")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.14 manifest findings mismatch")
    if manifest.get("safety") != report.get("safety"):
        errors.append("V9.14 manifest safety mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.14 manifest must not contain sidecar or ZIP hash fields")
    return errors


def validate_markdown_v9_14(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.14 markdown contains forbidden claim: {claim}")
    for phrase in ["aucun backtest", "aucun trading", "aucun ordre", "aucune strategie", "aucun signal actionnable", "aucun walk-forward"]:
        if phrase not in lowered:
            errors.append(f"V9.14 markdown missing safety phrase: {phrase}")
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.14 markdown contains forbidden metric term: {forbidden}")
    return errors


def validate_no_forbidden_artifacts_v9_14(root: Path) -> list[str]:
    errors: list[str] = []
    for path in [
        root / "data/research/v9_14",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models",
        root / "checkpoints",
    ]:
        if path.exists():
            errors.append(f"forbidden V9.14 artifact exists: {path}")
    for path in root.glob("projet-galapagos-v9.14-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.14 sidecar present: {path}")
    for path in root.rglob("*v9_14*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"forbidden V9.14 file present: {path}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden V9.14 file suffix present: {path}")
    return errors


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            text = str(key).casefold()
            if text == "zip_sha256" or text.startswith("sidecar_"):
                return True
            if _contains_forbidden_zip_field(value):
                return True
    if isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
