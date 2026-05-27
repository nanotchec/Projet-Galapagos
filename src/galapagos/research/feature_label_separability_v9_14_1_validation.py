from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.feature_label_separability_v9_14_1 import (
    ALLOWED_DECISIONS,
    CORRECTION_SCOPE,
    FINDINGS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    REQUIRED_SOURCE_NAMES,
    SAFETY,
    SAFETY_FLAGS,
    SOURCE_VERSION,
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


def validate_feature_label_separability_v9_14_1(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.exists():
        errors.append(f"missing V9.14.1 report: {REPORT_JSON_PATH}")
        return errors
    if not manifest_path.exists():
        errors.append(f"missing V9.14.1 manifest: {MANIFEST_PATH}")
        return errors
    if not markdown_path.exists():
        errors.append(f"missing V9.14.1 markdown: {REPORT_MD_PATH}")
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_14_1(report))
    errors.extend(validate_manifest_payload_v9_14_1(manifest, report))
    errors.extend(validate_markdown_v9_14_1(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_14_1(root))
    return errors


def validate_report_payload_v9_14_1(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.14.1 report version mismatch")
    if report.get("source_version") != SOURCE_VERSION:
        errors.append("V9.14.1 source_version mismatch")
    if report.get("correction_scope") != CORRECTION_SCOPE:
        errors.append("V9.14.1 correction_scope mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.14.1 status must be PASS")
    if report.get("previous_v9_14_decision") != "feature_first_before_more_labels":
        errors.append("V9.14.1 must preserve previous V9.14 decision")
    if report.get("corrected_decision") not in ALLOWED_DECISIONS:
        errors.append("V9.14.1 corrected decision is not allowed")
    if "backtest" in str(report.get("corrected_decision", "")).casefold():
        errors.append("V9.14.1 decision must not recommend a backtest")
    errors.extend(validate_inventory_payload_v9_14_1(report.get("data_source_inventory", []), report.get("corrected_decision")))
    errors.extend(validate_hypotheses_payload_v9_14_1(report.get("hypothesis_ranking", [])))
    if report.get("findings") != FINDINGS:
        errors.append("V9.14.1 findings mismatch")
    for key, expected in SAFETY.items():
        if report.get("safety", {}).get(key) is not expected:
            errors.append(f"V9.14.1 safety mismatch: {key}")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"V9.14.1 safety flag mismatch: {key}")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.14.1 report must not contain sidecar or ZIP hash fields")
    return errors


def validate_inventory_payload_v9_14_1(inventory: Any, corrected_decision: str | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(inventory, list) or not inventory:
        return ["V9.14.1 data_source_inventory must be a non-empty list"]
    names = {item.get("source_name") for item in inventory if isinstance(item, dict)}
    if names != set(REQUIRED_SOURCE_NAMES):
        errors.append("V9.14.1 inventory sources mismatch")
    required_fields = {
        "source_name",
        "present_in_repo",
        "used_in_validated_v9_chain",
        "evidence_paths",
        "known_quality",
        "known_coverage",
        "known_frequency",
        "causality_feasibility",
        "historical_availability",
        "leakage_risk",
        "integration_complexity",
        "potential_value",
        "recommended_priority",
        "notes",
    }
    for item in inventory:
        if not isinstance(item, dict):
            errors.append("V9.14.1 inventory item must be an object")
            continue
        missing = required_fields - set(item)
        if missing:
            errors.append(f"V9.14.1 inventory item missing fields: {sorted(missing)}")
        if item.get("present_in_repo") is True and not item.get("evidence_paths"):
            errors.append(f"V9.14.1 present source lacks evidence paths: {item.get('source_name')}")
        if item.get("source_name") in {"ohlcv", "public_trades_aggTrades"} and item.get("used_in_validated_v9_chain") is not True:
            errors.append(f"V9.14.1 V9 source must be marked used: {item.get('source_name')}")
    if corrected_decision == "data_extension_first_before_more_labels":
        priority = [
            item
            for item in inventory
            if isinstance(item, dict)
            and item.get("recommended_priority") == "priority_1_candidate"
            and item.get("present_in_repo") is True
            and item.get("used_in_validated_v9_chain") is False
        ]
        if not priority:
            errors.append("V9.14.1 data_extension decision requires a present priority_1 non-V9 source")
    return errors


def validate_hypotheses_payload_v9_14_1(hypotheses: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(hypotheses, list):
        return ["V9.14.1 hypotheses must be a list"]
    ids = {item.get("id") for item in hypotheses if isinstance(item, dict)}
    if ids != {f"H{index}" for index in range(1, 12)}:
        errors.append("V9.14.1 hypotheses H1-H11 must be complete")
    for item in hypotheses:
        if not isinstance(item, dict):
            errors.append("V9.14.1 hypothesis item must be an object")
            continue
        if item.get("status") not in {"likely", "possible", "unlikely", "unknown"}:
            errors.append(f"V9.14.1 hypothesis status invalid: {item.get('id')}")
        if not item.get("evidence_for") or not item.get("evidence_against") or not item.get("consequence_next_version"):
            errors.append(f"V9.14.1 hypothesis evidence incomplete: {item.get('id')}")
    return errors


def validate_manifest_payload_v9_14_1(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.14.1 manifest version mismatch")
    if manifest.get("source_version") != SOURCE_VERSION:
        errors.append("V9.14.1 manifest source_version mismatch")
    if manifest.get("correction_scope") != CORRECTION_SCOPE:
        errors.append("V9.14.1 manifest correction_scope mismatch")
    if manifest.get("status") != report.get("status"):
        errors.append("V9.14.1 manifest status mismatch")
    if manifest.get("corrected_decision") != report.get("corrected_decision"):
        errors.append("V9.14.1 manifest decision mismatch")
    if manifest.get("data_source_inventory_count") != len(report.get("data_source_inventory", [])):
        errors.append("V9.14.1 manifest inventory count mismatch")
    if manifest.get("hypotheses_count") != len(report.get("hypothesis_ranking", [])):
        errors.append("V9.14.1 manifest hypotheses count mismatch")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.14.1 manifest findings mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.14.1 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.14.1 manifest must not contain sidecar or ZIP hash fields")
    return errors


def validate_markdown_v9_14_1(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.14.1 markdown contains forbidden claim: {claim}")
    for phrase in ["aucun backtest", "aucun trading", "aucun ordre", "aucune strategie", "aucun signal actionnable", "aucun walk-forward"]:
        if phrase not in lowered:
            errors.append(f"V9.14.1 markdown missing safety phrase: {phrase}")
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.14.1 markdown contains forbidden metric term: {forbidden}")
    if "h11" not in lowered or "data-extension" not in lowered:
        errors.append("V9.14.1 markdown must mention H11 and data-extension")
    return errors


def validate_no_forbidden_artifacts_v9_14_1(root: Path) -> list[str]:
    errors: list[str] = []
    for path in [
        root / "data/research/v9_14_1",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models",
        root / "checkpoints",
    ]:
        if path.exists():
            errors.append(f"forbidden V9.14.1 artifact exists: {path}")
    for path in root.glob("projet-galapagos-v9.14.1-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.14.1 sidecar present: {path}")
    for path in root.rglob("*v9_14_1*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"forbidden V9.14.1 file present: {path}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden V9.14.1 file suffix present: {path}")
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
