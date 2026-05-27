from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.ml.h4_label_candidate_offline_ml_v9_13 import (
    FINDINGS_V9_13,
    MANIFEST_PATH_ML_V9_13,
    ML_SCORE_COLUMNS_V9_13,
    MODEL_NAMES_V9_13,
    REPORT_JSON_PATH_ML_V9_13,
    REPORT_MD_PATH_ML_V9_13,
    SAFETY_FLAGS_ML_V9_13,
    TARGET_NAME_V9_13,
    TIMEFRAMES_V9_13,
    VERSION_V9_13_ML,
)


ALLOWED_ML_DECISIONS = {
    "h4_offline_ml_diagnostic_completed",
    "h4_offline_ml_completed_but_weak_vs_baselines",
    "h4_offline_ml_completed_but_close_to_shuffled_labels",
    "h4_offline_ml_not_ready_dataset_issue",
    "stop_h4_candidate_ml_failed",
}
ALLOWED_GLOBAL_DECISIONS = {
    "h4_candidate_ready_for_strict_walk_forward_diagnostic",
    "h4_candidate_not_ready_refine_labels_again",
    "h4_candidate_not_ready_feature_first",
    "h4_candidate_not_ready_extend_data_first",
    "stop_h4_candidate_branch",
}
FORBIDDEN_CLAIMS = ["strategy validated", "tradable edge confirmed", "live trading ready", "profitability confirmed"]


def validate_h4_label_candidate_offline_ml_v9_13(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for path in [REPORT_JSON_PATH_ML_V9_13, MANIFEST_PATH_ML_V9_13, REPORT_MD_PATH_ML_V9_13]:
        if not (root / path).exists():
            errors.append(f"missing V9.13 ML artifact: {path}")
    if errors:
        return errors
    report = _read_json(root / REPORT_JSON_PATH_ML_V9_13)
    manifest = _read_json(root / MANIFEST_PATH_ML_V9_13)
    errors.extend(validate_ml_report_payload_v9_13(report))
    errors.extend(validate_ml_manifest_payload_v9_13(manifest, report))
    errors.extend(validate_ml_markdown_v9_13((root / REPORT_MD_PATH_ML_V9_13).read_text(encoding="utf-8")))
    errors.extend(validate_ml_outputs_v9_13(root, report))
    errors.extend(validate_no_forbidden_ml_artifacts_v9_13(root))
    return errors


def validate_ml_report_payload_v9_13(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION_V9_13_ML:
        errors.append("V9.13 ML report version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.13 ML status must be PASS")
    if report.get("decision") not in ALLOWED_ML_DECISIONS:
        errors.append("V9.13 ML decision is not allowed")
    if report.get("global_decision", {}).get("decision") not in ALLOWED_GLOBAL_DECISIONS:
        errors.append("V9.13 global decision is not allowed")
    if report.get("target_name") != TARGET_NAME_V9_13:
        errors.append("V9.13 ML target mismatch")
    if report.get("models") != MODEL_NAMES_V9_13:
        errors.append("V9.13 ML models mismatch")
    if report.get("feature_leakage_scan", {}).get("passed") is not True:
        errors.append("V9.13 ML leakage scan must pass")
    if report.get("metric_forbidden_scan", {}).get("passed") is not True:
        errors.append("V9.13 ML forbidden metric scan must pass")
    if report.get("findings") != FINDINGS_V9_13:
        errors.append("V9.13 ML findings mismatch")
    for key, expected in SAFETY_FLAGS_ML_V9_13.items():
        if report.get("safety", {}).get(key) is not expected:
            errors.append(f"V9.13 ML safety mismatch: {key}")
    if "zip_sha256" in report or any(str(key).startswith("sidecar_") for key in report):
        errors.append("V9.13 ML report must not contain ZIP hash or sidecar fields")
    return errors


def validate_ml_manifest_payload_v9_13(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != report.get("version"):
        errors.append("V9.13 ML manifest version mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("V9.13 ML manifest decision mismatch")
    if manifest.get("target_name") != TARGET_NAME_V9_13:
        errors.append("V9.13 ML manifest target mismatch")
    if "zip_sha256" in manifest or any(str(key).startswith("sidecar_") for key in manifest):
        errors.append("V9.13 ML manifest must not contain ZIP hash or sidecar fields")
    return errors


def validate_ml_outputs_v9_13(root: Path, report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for timeframe in TIMEFRAMES_V9_13:
        path = root / report.get("outputs", {}).get(timeframe, {}).get("path", "")
        if not path.is_file():
            errors.append(f"missing V9.13 ML scores: {timeframe}")
            continue
        frame = pd.read_parquet(path, engine="pyarrow")
        if list(frame.columns) != ML_SCORE_COLUMNS_V9_13:
            errors.append(f"V9.13 ML score schema mismatch: {timeframe}")
        if set(frame["model_name"].dropna().unique().tolist()) != set(MODEL_NAMES_V9_13):
            errors.append(f"V9.13 ML model set mismatch: {timeframe}")
        if frame["target_name"].dropna().nunique() != 1 or frame["target_name"].dropna().iloc[0] != TARGET_NAME_V9_13:
            errors.append(f"V9.13 ML target mismatch in scores: {timeframe}")
        forbidden = [column for column in frame.columns if column.casefold() in {"signal", "trading_signal", "order", "pnl", "backtest", "strategy", "model_score"}]
        if forbidden:
            errors.append(f"V9.13 ML forbidden score columns: {forbidden}")
    return errors


def validate_ml_markdown_v9_13(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.13 ML markdown contains forbidden claim: {claim}")
    for phrase in ["aucun backtest", "aucune strategie", "aucun signal actionnable", "aucun ordre", "aucun modele persistant", "aucun trading"]:
        if phrase not in lowered:
            errors.append(f"V9.13 ML markdown missing safety phrase: {phrase}")
    return errors


def validate_no_forbidden_ml_artifacts_v9_13(root: Path) -> list[str]:
    errors: list[str] = []
    forbidden = [
        root / "data/research/v9_13/backtests",
        root / "data/research/v9_13/strategies",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models",
        root / "checkpoints",
    ]
    for path in forbidden:
        if path.exists():
            errors.append(f"forbidden artifact exists: {path}")
    for path in root.glob("projet-galapagos-v9.13-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden sidecar exists: {path}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
