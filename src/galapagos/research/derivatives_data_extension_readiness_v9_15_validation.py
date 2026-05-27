from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.derivatives_data_extension_readiness_v9_15 import (
    ALLOWED_DECISIONS,
    FINDINGS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY,
    SAFETY_FLAGS,
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


def validate_derivatives_data_extension_readiness_v9_15(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.exists():
        errors.append(f"missing V9.15 report: {REPORT_JSON_PATH}")
        return errors
    if not manifest_path.exists():
        errors.append(f"missing V9.15 manifest: {MANIFEST_PATH}")
        return errors
    if not markdown_path.exists():
        errors.append(f"missing V9.15 markdown: {REPORT_MD_PATH}")
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_15(report))
    errors.extend(validate_manifest_payload_v9_15(manifest, report))
    errors.extend(validate_markdown_v9_15(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_15(root))
    return errors


def validate_report_payload_v9_15(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.15 report version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.15 status must be PASS")
    decision = report.get("v9_15_decision", {})
    if decision.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.15 decision is not allowed")
    if "backtest" in str(decision.get("decision", "")).casefold():
        errors.append("V9.15 decision must not recommend a backtest")
    if report.get("features_candidate_created") is not False:
        errors.append("V9.15 should not create features when V9 window is incompatible")
    funding = report.get("funding_readiness", {})
    open_interest = report.get("open_interest_readiness", {})
    errors.extend(validate_source_readiness_v9_15(funding, "funding_rates"))
    errors.extend(validate_source_readiness_v9_15(open_interest, "open_interest"))
    compatibility = report.get("v9_chain_compatibility", {})
    if compatibility.get("compatible_with_current_v9_chain") is not False:
        errors.append("V9.15 must mark current V9 chain as incompatible with local funding/OI coverage")
    if compatibility.get("alignment_possible_now") is not False:
        errors.append("V9.15 alignment_possible_now must be false")
    if report.get("feature_candidate", {}).get("created") is not False:
        errors.append("V9.15 feature candidate must not be created")
    if report.get("findings") != FINDINGS:
        errors.append("V9.15 findings mismatch")
    for key, expected in SAFETY.items():
        if report.get("safety", {}).get(key) is not expected:
            errors.append(f"V9.15 safety mismatch: {key}")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"V9.15 safety flag mismatch: {key}")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.15 report must not contain sidecar or ZIP hash fields")
    return errors


def validate_source_readiness_v9_15(payload: dict[str, Any], expected_source_name: str) -> list[str]:
    errors: list[str] = []
    if payload.get("source_name") != expected_source_name:
        errors.append(f"V9.15 source readiness mismatch: {expected_source_name}")
    if payload.get("present_local") is not True:
        errors.append(f"V9.15 source should be present in reports: {expected_source_name}")
    if not payload.get("evidence_paths"):
        errors.append(f"V9.15 source lacks evidence paths: {expected_source_name}")
    if payload.get("compatible_with_v9_window") is not False:
        errors.append(f"V9.15 source must not overlap current V9 window: {expected_source_name}")
    if payload.get("readiness_decision") != "not_ready_missing_coverage":
        errors.append(f"V9.15 source readiness must be missing coverage: {expected_source_name}")
    checks = payload.get("coverage_checks", [])
    if not checks:
        errors.append(f"V9.15 source coverage checks missing: {expected_source_name}")
    if any(item.get("overlaps_v9_window") for item in checks):
        errors.append(f"V9.15 coverage check unexpectedly overlaps V9: {expected_source_name}")
    return errors


def validate_manifest_payload_v9_15(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.15 manifest version mismatch")
    if manifest.get("status") != report.get("status"):
        errors.append("V9.15 manifest status mismatch")
    if manifest.get("v9_15_decision", {}).get("decision") != report.get("v9_15_decision", {}).get("decision"):
        errors.append("V9.15 manifest decision mismatch")
    if manifest.get("features_candidate_created") is not False:
        errors.append("V9.15 manifest must mark features_candidate_created=false")
    if manifest.get("compatible_with_current_v9_chain") is not False:
        errors.append("V9.15 manifest compatibility mismatch")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.15 manifest findings mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.15 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.15 manifest must not contain sidecar or ZIP hash fields")
    return errors


def validate_markdown_v9_15(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.15 markdown contains forbidden claim: {claim}")
    for phrase in ["aucun backtest", "aucun trading", "aucun ordre", "aucune strategie", "aucun signal actionnable", "aucun walk-forward"]:
        if phrase not in lowered:
            errors.append(f"V9.15 markdown missing safety phrase: {phrase}")
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.15 markdown contains forbidden metric term: {forbidden}")
    if "funding readiness" not in lowered or "open interest readiness" not in lowered:
        errors.append("V9.15 markdown must mention funding and open interest readiness")
    if "aucun reseau" not in lowered or "aucun telechargement" not in lowered:
        errors.append("V9.15 markdown must confirm no network and no download")
    return errors


def validate_no_forbidden_artifacts_v9_15(root: Path) -> list[str]:
    errors: list[str] = []
    for path in [
        root / "data/research/v9_15",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models",
        root / "checkpoints",
    ]:
        if path.exists():
            errors.append(f"forbidden V9.15 artifact exists: {path}")
    for path in root.glob("projet-galapagos-v9.15-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.15 sidecar present: {path}")
    for path in root.rglob("*v9_15*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"forbidden V9.15 file present: {path}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden V9.15 file suffix present: {path}")
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
