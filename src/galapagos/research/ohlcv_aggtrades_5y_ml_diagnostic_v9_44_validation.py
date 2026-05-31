from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.ohlcv_aggtrades_5y_ml_diagnostic_v9_44 import FINDINGS, MANIFEST_PATH, REPORT_JSON_PATH, REPORT_MD_PATH, SAFETY_FLAGS, VERSION


ALLOWED_DECISIONS = {
    "feature_enrichment_before_more_ml",
    "label_redesign_before_more_ml",
    "derivatives_data_extension_before_more_ml",
    "ml_diagnostic_inconclusive_manual_review_required",
    "walk_forward_not_justified",
    "stop_5y_ml_branch",
}
FORBIDDEN_PHRASES = ["tradable edge", "live trading ready", "strategy validated", "profitability confirmed"]


def validate_ml_diagnostic_v9_44(root: Path = Path("."), *, audit_lite: bool = False) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for path in [REPORT_JSON_PATH, REPORT_MD_PATH, MANIFEST_PATH]:
        if not (root / path).is_file():
            errors.append(f"missing V9.44 artifact: {path}")
    if errors:
        return errors
    report = _read_json(root / REPORT_JSON_PATH)
    manifest = _read_json(root / MANIFEST_PATH)
    errors.extend(validate_report_payload_v9_44(report))
    errors.extend(validate_manifest_payload_v9_44(manifest, report))
    errors.extend(validate_markdown_v9_44((root / REPORT_MD_PATH).read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_44(root, audit_lite=audit_lite))
    return errors


def validate_report_payload_v9_44(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.43":
        errors.append("V9.44 report version/source mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.44 decision is not allowed")
    if report.get("diagnostic_only") is not True or report.get("heavy_ml_executed") is not False:
        errors.append("V9.44 must remain diagnostic-only without heavy ML")
    for key in ["walk_forward_executed", "backtest_executed", "signal_created", "strategy_created", "model_persisted", "network_used", "new_data_downloaded"]:
        if report.get(key) is not False:
            errors.append(f"V9.44 forbidden execution flag must be false: {key}")
    if report.get("findings") != FINDINGS:
        errors.append("V9.44 findings mismatch")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"V9.44 safety flag mismatch: {key}")
    ml = report.get("ml_result_summary", {})
    if ml.get("baseline_clear_wins_count") != 0:
        errors.append("V9.44 expected no baseline clear wins from V9.43")
    if ml.get("no_clear_edge_vs_shuffled_labels_count", 0) < 1:
        errors.append("V9.44 expected close-to-shuffled warnings")
    if "feature_diagnostic" not in report or "label_diagnostic" not in report or "option_comparison" not in report:
        errors.append("V9.44 report must contain diagnostic sections")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.44 report contains forbidden ZIP fingerprint or sidecar field")
    return errors


def validate_manifest_payload_v9_44(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION or manifest.get("source_version") != "V9.43":
        errors.append("V9.44 manifest version/source mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("V9.44 manifest decision mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.44 manifest safety flags mismatch")
    if manifest.get("sidecars_created") is not False or manifest.get("zip_fingerprints_created") is not False:
        errors.append("V9.44 manifest must confirm no sidecars and no ZIP fingerprints")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.44 manifest contains forbidden ZIP fingerprint or sidecar field")
    return errors


def validate_markdown_v9_44(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            errors.append(f"V9.44 markdown contains forbidden claim: {phrase}")
    for phrase in ["aucun backtest", "aucun walk-forward", "aucune strategie", "aucun signal actionnable", "aucun modele persistant", "aucun reseau"]:
        if phrase not in lowered:
            errors.append(f"V9.44 markdown missing safety phrase: {phrase}")
    return errors


def validate_no_forbidden_artifacts_v9_44(root: Path, *, audit_lite: bool = False) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if any(part in {".venv", "__pycache__", ".git", ".pytest_cache", ".mypy_cache", ".ruff_cache"} for part in path.relative_to(root).parts):
            continue
        if relative.startswith("projet-galapagos-v9.44-audit-lite.zip"):
            continue
        if "v9.44" in path.name.casefold() and path.name.endswith((".sha256.json", ".sha256.txt")):
            errors.append(f"forbidden V9.44 sidecar artifact: {relative}")
        if "v9_44" in relative.casefold() and path.name.endswith((".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt")):
            errors.append(f"forbidden V9.44 persistent model artifact: {relative}")
    if audit_lite:
        for prefix in ["data/research/", "data/raw/", "data/silver/"]:
            if (root / prefix).exists():
                errors.append(f"audit-lite must not include full data directory: {prefix}")
    return errors


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).casefold()
            if "zip_sha256" in lowered or lowered.endswith("_sha256") or lowered == "sha256":
                return True
            if _contains_forbidden_zip_field(value):
                return True
    elif isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
