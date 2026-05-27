from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.refined_volnorm_research_decision_gate_v9_10 import (
    ALLOWED_DECISIONS_V9_10,
    FINDINGS_V9_10,
    MANIFEST_PATH_V9_10,
    REPORT_JSON_PATH_V9_10,
    REPORT_MD_PATH_V9_10,
    SAFETY_FLAGS_V9_10,
    VERSION_V9_10,
)


FORBIDDEN_CLAIMS_V9_10 = ["strategy validated", "tradable edge confirmed", "live trading ready", "profitability confirmed"]


def validate_refined_volnorm_research_decision_gate_v9_10(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    for path in [MANIFEST_PATH_V9_10, REPORT_JSON_PATH_V9_10, REPORT_MD_PATH_V9_10]:
        if not (root / path).exists():
            return _result([f"missing V9.10 file: {path}"], warnings)
    report = _read_json(root / REPORT_JSON_PATH_V9_10)
    manifest = _read_json(root / MANIFEST_PATH_V9_10)
    errors.extend(validate_report_payload_v9_10(report))
    errors.extend(validate_manifest_payload_v9_10(manifest, report))
    errors.extend(validate_markdown_v9_10((root / REPORT_MD_PATH_V9_10).read_text(encoding="utf-8")))
    return _result(errors, warnings, report)


def validate_report_payload_v9_10(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION_V9_10:
        errors.append("V9.10 version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.10 status must be PASS")
    if report.get("decision_gate_type") != "research_only":
        errors.append("V9.10 decision_gate_type mismatch")
    if report.get("research_decision") not in ALLOWED_DECISIONS_V9_10:
        errors.append("V9.10 research decision is not allowed")
    if report.get("findings") != FINDINGS_V9_10:
        errors.append("V9.10 findings mismatch")
    if report.get("safety") != SAFETY_FLAGS_V9_10:
        errors.append("V9.10 safety mismatch")
    if report.get("leakage_assessment", {}).get("passed") is not True:
        errors.append("V9.10 leakage assessment must pass")
    if report.get("metric_forbidden_scan", {}).get("passed") is not True:
        errors.append("V9.10 forbidden metric scan must pass")
    if not report.get("next_step_recommendation"):
        errors.append("V9.10 next step missing")
    return errors


def validate_manifest_payload_v9_10(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION_V9_10:
        errors.append("V9.10 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V9.10 manifest status must be PASS")
    if manifest.get("research_decision") != report.get("research_decision"):
        errors.append("V9.10 manifest decision mismatch")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.10 manifest findings mismatch")
    if manifest.get("safety") != report.get("safety"):
        errors.append("V9.10 manifest safety mismatch")
    return errors


def validate_markdown_v9_10(text: str) -> list[str]:
    lowered = text.casefold()
    errors = [f"markdown contains forbidden claim: {claim}" for claim in FORBIDDEN_CLAIMS_V9_10 if claim in lowered]
    for required in ["aucun backtest", "aucune strategie", "aucun signal actionnable", "aucun ordre", "aucun trading reel"]:
        if required not in lowered:
            errors.append(f"markdown missing required phrase: {required}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(errors: list[str], warnings: list[str], report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION_V9_10, "passed": not errors, "errors": errors, "warnings": warnings, "report": report or {}}
