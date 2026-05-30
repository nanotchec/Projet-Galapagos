from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_41_schemas import FEATURE_COLUMNS, SELECTED_PRIMARY_LABEL, TIMEFRAMES
from galapagos.ml.ohlcv_aggtrades_5y_offline_ml_v9_43 import (
    FINDINGS,
    MANIFEST_PATH,
    MODEL_NAMES,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY_FLAGS,
    SCORES_JSON_PATH,
    TARGET_NAME,
    VERSION,
)


ALLOWED_DECISIONS = {
    "offline_ml_5y_completed",
    "offline_ml_5y_completed_but_weak_vs_baselines",
    "offline_ml_5y_completed_but_close_to_shuffled_labels",
    "offline_ml_5y_blocked_by_dataset_issue",
    "offline_ml_5y_blocked_by_leakage",
    "offline_ml_5y_blocked_by_forbidden_metrics",
    "stop_5y_ml_branch",
}

FORBIDDEN_CLAIMS = ["tradable edge", "live trading ready", "profitability confirmed", "strategy validated"]


def validate_offline_ml_v9_43(root: Path = Path("."), *, audit_lite: bool = False) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for path in [REPORT_JSON_PATH, REPORT_MD_PATH, SCORES_JSON_PATH, MANIFEST_PATH]:
        if not (root / path).is_file():
            errors.append(f"missing V9.43 artifact: {path}")
    if errors:
        return errors
    report = _read_json(root / REPORT_JSON_PATH)
    scores = _read_json(root / SCORES_JSON_PATH)
    manifest = _read_json(root / MANIFEST_PATH)
    errors.extend(validate_report_payload_v9_43(report))
    errors.extend(validate_scores_payload_v9_43(scores, report))
    errors.extend(validate_manifest_payload_v9_43(manifest, report))
    errors.extend(validate_markdown_v9_43((root / REPORT_MD_PATH).read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_43(root, audit_lite=audit_lite))
    return errors


def validate_report_payload_v9_43(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION or report.get("source_version") != "V9.42":
        errors.append("V9.43 report version/source mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.43 decision is not allowed")
    if report.get("target_name") != SELECTED_PRIMARY_LABEL or report.get("target") != TARGET_NAME:
        errors.append("V9.43 target mismatch")
    if report.get("feature_columns") != list(FEATURE_COLUMNS) or report.get("feature_columns_count") != len(FEATURE_COLUMNS):
        errors.append("V9.43 feature columns mismatch")
    if report.get("models_executed") != MODEL_NAMES:
        errors.append("V9.43 models mismatch")
    if report.get("train_only_fit") is not True or report.get("validation_test_not_used_for_fit") is not True:
        errors.append("V9.43 must confirm train-only fit")
    if report.get("walk_forward_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.43 must not run walk-forward or backtest")
    if report.get("signal_created") is not False or report.get("strategy_created") is not False:
        errors.append("V9.43 must not create signal or strategy")
    if report.get("model_persisted") is not False:
        errors.append("V9.43 must not persist models")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False:
        errors.append("V9.43 must not use network or download data")
    if report.get("forbidden_feature_scan", {}).get("status") != "PASS":
        errors.append("V9.43 forbidden feature scan must pass")
    if report.get("forbidden_metric_scan", {}).get("status") != "PASS":
        errors.append("V9.43 forbidden metric scan must pass")
    if report.get("no_persistent_model_check", {}).get("status") != "PASS":
        errors.append("V9.43 no persistent model check must pass")
    if report.get("findings") != FINDINGS:
        errors.append("V9.43 findings mismatch")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"V9.43 safety flag mismatch: {key}")
    for timeframe in TIMEFRAMES:
        if timeframe not in report.get("model_results_by_timeframe", {}):
            errors.append(f"missing V9.43 timeframe results: {timeframe}")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.43 report contains forbidden sidecar or ZIP fingerprint field")
    return errors


def validate_scores_payload_v9_43(scores: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if scores.get("version") != VERSION:
        errors.append("V9.43 scores version mismatch")
    if scores.get("contains_predictions") is not False or scores.get("contains_actionable_signal") is not False:
        errors.append("V9.43 scores must remain aggregate-only and non-actionable")
    if scores.get("model_results_by_split") != report.get("model_results_by_split"):
        errors.append("V9.43 scores/report split metrics mismatch")
    if _contains_forbidden_zip_field(scores):
        errors.append("V9.43 scores contain forbidden sidecar or ZIP fingerprint field")
    return errors


def validate_manifest_payload_v9_43(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION or manifest.get("source_version") != "V9.42":
        errors.append("V9.43 manifest version/source mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("V9.43 manifest decision mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.43 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.43 manifest contains forbidden sidecar or ZIP fingerprint field")
    return errors


def validate_markdown_v9_43(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.43 markdown contains forbidden claim: {claim}")
    for phrase in ["aucun backtest", "aucun walk-forward", "aucune strategie", "aucun signal actionnable", "aucun modele persistant", "aucun reseau"]:
        if phrase not in lowered:
            errors.append(f"V9.43 markdown missing safety phrase: {phrase}")
    return errors


def validate_no_forbidden_artifacts_v9_43(root: Path, *, audit_lite: bool = False) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if any(part in {".venv", "__pycache__", ".git", ".pytest_cache", ".mypy_cache", ".ruff_cache"} for part in path.relative_to(root).parts):
            continue
        if relative.startswith("projet-galapagos-v9.43-audit-lite.zip"):
            continue
        if path.name.endswith((".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt")):
            errors.append(f"forbidden persistent model artifact: {relative}")
        if "v9.43" in path.name.casefold() and path.name.endswith((".sha256.json", ".sha256.txt")):
            errors.append(f"forbidden sidecar artifact: {relative}")
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
