from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.ml.redesigned_label_5y_offline_ml_v9_66 import FINDINGS, MANIFEST_PATH, REPORT_JSON_PATH, SAFETY_FLAGS, SCORES_JSON_PATH, TARGET_NAME, VERSION


ALLOWED_DECISIONS = {
    "redesigned_label_ml_completed_with_improvement",
    "redesigned_label_ml_completed_but_weak_vs_baselines",
    "redesigned_label_ml_completed_but_close_to_shuffled",
    "redesigned_label_ml_completed_but_class_collapse",
    "redesigned_label_ml_blocked_by_dataset_issue",
    "redesigned_label_ml_blocked_by_leakage",
}


def validate_redesigned_label_5y_offline_ml_v9_66(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    report_path = root / REPORT_JSON_PATH
    scores_path = root / SCORES_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    if not report_path.is_file():
        return [f"missing report: {REPORT_JSON_PATH}"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    errors = validate_report_payload_v9_66(report)
    if not scores_path.is_file():
        errors.append(f"missing scores: {SCORES_JSON_PATH}")
    else:
        errors.extend(validate_scores_payload_v9_66(json.loads(scores_path.read_text(encoding="utf-8")), report))
    if not manifest_path.is_file():
        errors.append(f"missing manifest: {MANIFEST_PATH}")
    else:
        errors.extend(validate_manifest_payload_v9_66(json.loads(manifest_path.read_text(encoding="utf-8")), report))
    return errors


def validate_report_payload_v9_66(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("version mismatch")
    if report.get("decision") not in ALLOWED_DECISIONS:
        errors.append("invalid decision")
    if report.get("target_name") != TARGET_NAME:
        errors.append("target mismatch")
    for key, expected in {"walk_forward_executed": False, "backtest_executed": False, "signal_created": False, "strategy_created": False, "model_persisted": False, "network_used": False, "new_data_downloaded": False}.items():
        if report.get(key) is not expected:
            errors.append(f"{key} must be {expected}")
    if report.get("forbidden_metric_scan", {}).get("status") != "PASS":
        errors.append("forbidden metric scan must pass")
    if report.get("no_persistent_model_check", {}).get("status") != "PASS":
        errors.append("no persistent model check must pass")
    if not report.get("model_results_by_split") and report.get("status") == "PASS":
        errors.append("missing model results")
    if report.get("findings") != FINDINGS:
        errors.append("findings mismatch")
    flags = report.get("safety_flags", {})
    for key, expected in SAFETY_FLAGS.items():
        if flags.get(key) is not expected:
            errors.append(f"safety flag mismatch: {key}")
    return errors


def validate_scores_payload_v9_66(scores: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if scores.get("version") != VERSION:
        errors.append("scores version mismatch")
    if scores.get("contains_predictions") is not False:
        errors.append("scores must not persist predictions")
    if scores.get("contains_actionable_signal") is not False:
        errors.append("scores must not contain actionable signal")
    if scores.get("model_results_by_split") != report.get("model_results_by_split", {}):
        errors.append("scores model results mismatch")
    return errors


def validate_manifest_payload_v9_66(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("manifest version mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("manifest decision mismatch")
    if manifest.get("target_name") != report.get("target_name"):
        errors.append("manifest target mismatch")
    return errors
