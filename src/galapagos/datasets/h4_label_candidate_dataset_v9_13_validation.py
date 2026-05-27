from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.datasets.h4_label_candidate_dataset_v9_13_schemas import (
    ALLOWED_DATASET_DECISIONS_V9_13,
    DATASET_COLUMNS_V9_13,
    EXPECTED_ROWS_V9_13,
    FINDINGS_V9_13,
    FORBIDDEN_DATASET_COLUMNS_V9_13,
    MANIFEST_PATH_DATASET_V9_13,
    REPORT_JSON_PATH_DATASET_V9_13,
    REPORT_MD_PATH_DATASET_V9_13,
    SAFETY_FLAGS_DATASET_V9_13,
    TARGET_NAME_V9_13,
    TIMEFRAMES_V9_13,
    VERSION_V9_13_DATASET,
)


FORBIDDEN_CLAIMS = ["strategy validated", "tradable edge confirmed", "live trading ready", "profitability confirmed"]


def validate_h4_label_candidate_dataset_v9_13(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for path in [REPORT_JSON_PATH_DATASET_V9_13, MANIFEST_PATH_DATASET_V9_13, REPORT_MD_PATH_DATASET_V9_13]:
        if not (root / path).exists():
            errors.append(f"missing V9.13 dataset artifact: {path}")
    if errors:
        return errors
    report = _read_json(root / REPORT_JSON_PATH_DATASET_V9_13)
    manifest = _read_json(root / MANIFEST_PATH_DATASET_V9_13)
    errors.extend(validate_dataset_report_payload_v9_13(report))
    errors.extend(validate_dataset_manifest_payload_v9_13(manifest, report))
    errors.extend(validate_dataset_markdown_v9_13((root / REPORT_MD_PATH_DATASET_V9_13).read_text(encoding="utf-8")))
    errors.extend(validate_dataset_outputs_v9_13(root, report))
    errors.extend(validate_no_forbidden_dataset_artifacts_v9_13(root))
    return errors


def validate_dataset_report_payload_v9_13(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION_V9_13_DATASET:
        errors.append("V9.13 dataset report version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.13 dataset status must be PASS")
    if report.get("decision") not in ALLOWED_DATASET_DECISIONS_V9_13:
        errors.append("V9.13 dataset decision is not allowed")
    if report.get("target_name") != TARGET_NAME_V9_13:
        errors.append("V9.13 dataset target mismatch")
    if report.get("dataset_columns") != DATASET_COLUMNS_V9_13:
        errors.append("V9.13 dataset schema mismatch")
    if report.get("leakage_guard", {}).get("passed") is not True:
        errors.append("V9.13 dataset leakage guard must pass")
    if report.get("findings") != FINDINGS_V9_13:
        errors.append("V9.13 dataset findings mismatch")
    for key, expected in SAFETY_FLAGS_DATASET_V9_13.items():
        if report.get("safety", {}).get(key) is not expected:
            errors.append(f"V9.13 dataset safety mismatch: {key}")
    return errors


def validate_dataset_manifest_payload_v9_13(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != report.get("version"):
        errors.append("V9.13 dataset manifest version mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("V9.13 dataset manifest decision mismatch")
    if manifest.get("dataset_columns") != DATASET_COLUMNS_V9_13:
        errors.append("V9.13 dataset manifest schema mismatch")
    if "zip_sha256" in manifest or any(str(key).startswith("sidecar_") for key in manifest):
        errors.append("V9.13 dataset manifest must not contain ZIP hash or sidecar fields")
    return errors


def validate_dataset_outputs_v9_13(root: Path, report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for timeframe in TIMEFRAMES_V9_13:
        path = root / report.get("outputs", {}).get(timeframe, {}).get("path", "")
        if not path.is_file():
            errors.append(f"missing V9.13 dataset output: {timeframe}")
            continue
        frame = pd.read_parquet(path, engine="pyarrow")
        if list(frame.columns) != DATASET_COLUMNS_V9_13:
            errors.append(f"V9.13 dataset columns mismatch: {timeframe}")
        if len(frame) != EXPECTED_ROWS_V9_13[timeframe]:
            errors.append(f"V9.13 dataset row count mismatch: {timeframe}")
        forbidden = [column for column in frame.columns if column.casefold() in FORBIDDEN_DATASET_COLUMNS_V9_13]
        if forbidden:
            errors.append(f"V9.13 forbidden dataset columns {timeframe}: {forbidden}")
        if frame["target_name"].dropna().nunique() != 1 or frame["target_name"].dropna().iloc[0] != TARGET_NAME_V9_13:
            errors.append(f"V9.13 target_name mismatch in dataset: {timeframe}")
        valid = frame["label_valid"] == True  # noqa: E712
        if valid.any() and not (pd.to_datetime(frame.loc[valid, "label_available_ts"], utc=True) > pd.to_datetime(frame.loc[valid, "decision_ts"], utc=True)).all():
            errors.append(f"V9.13 label availability violation: {timeframe}")
        if not (pd.to_datetime(frame["feature_available_ts"], utc=True) <= pd.to_datetime(frame["decision_ts"], utc=True)).all():
            errors.append(f"V9.13 feature availability violation: {timeframe}")
    return errors


def validate_dataset_markdown_v9_13(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.13 dataset markdown contains forbidden claim: {claim}")
    for phrase in ["aucun backtest", "aucune strategie", "aucun signal actionnable", "aucun ordre", "aucun trading"]:
        if phrase not in lowered:
            errors.append(f"V9.13 dataset markdown missing safety phrase: {phrase}")
    return errors


def validate_no_forbidden_dataset_artifacts_v9_13(root: Path) -> list[str]:
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
