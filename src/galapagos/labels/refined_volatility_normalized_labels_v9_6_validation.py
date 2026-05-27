from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.labels.refined_volatility_normalized_labels_v9_6 import assess_label_quality_v9_6
from galapagos.labels.refined_volatility_normalized_labels_v9_6_schemas import (
    ALLOWED_DECISIONS_V9_6,
    EXPECTED_LIMITATIONS_V9_6,
    EXPECTED_ROWS_V9_6,
    FINDINGS_V9_6,
    FORBIDDEN_LABEL_COLUMNS_V9_6,
    INPUT_DATASET_MANIFEST_V9_1,
    LABEL_SCHEMA_VERSION_V9_6,
    MANIFEST_PATH_V9_6,
    PARAMETER_GRID_V9_6,
    REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6,
    REPORT_JSON_PATH_V9_6,
    REPORT_MD_PATH_V9_6,
    SAFETY_FLAGS_V9_6,
    TARGET_NAME_V9_6,
    TIMEFRAMES_V9_6,
    VERSION_V9_6,
    get_refined_volnorm_label_path_v9_6,
)


FORBIDDEN_CLAIMS_V9_6 = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "profitability confirmed",
]


def validate_refined_volatility_normalized_labels_v9_6(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = root / MANIFEST_PATH_V9_6
    report_path = root / REPORT_JSON_PATH_V9_6
    markdown_path = root / REPORT_MD_PATH_V9_6
    if not manifest_path.exists():
        return _result([f"missing manifest: {MANIFEST_PATH_V9_6}"], warnings)
    if not report_path.exists():
        return _result([f"missing report: {REPORT_JSON_PATH_V9_6}"], warnings)
    if not markdown_path.exists():
        return _result([f"missing markdown: {REPORT_MD_PATH_V9_6}"], warnings)

    manifest = _read_json(manifest_path)
    report = _read_json(report_path)
    dataset_manifest = _read_json(root / INPUT_DATASET_MANIFEST_V9_1)
    errors.extend(validate_manifest_payload_v9_6(manifest))
    errors.extend(validate_report_payload_v9_6(report))
    errors.extend(_validate_markdown(markdown_path.read_text(encoding="utf-8")))
    if errors:
        return _result(errors, warnings, manifest)

    physical_quality: dict[str, Any] = {}
    for timeframe in TIMEFRAMES_V9_6:
        dataset_path = root / dataset_manifest["outputs"][timeframe]["path"]
        label_path = get_refined_volnorm_label_path_v9_6(root, timeframe)
        if not label_path.exists():
            errors.append(f"missing labels for {timeframe}: {label_path.relative_to(root)}")
            continue
        labels = read_parquet(label_path)
        dataset = read_parquet(dataset_path)
        errors.extend(validate_label_frame_v9_6(labels, timeframe))
        if manifest["outputs"][timeframe]["sha256"] != sha256_file(label_path):
            errors.append(f"labels sha256 mismatch for {timeframe}")
        if manifest["outputs"][timeframe]["rows"] != len(labels):
            errors.append(f"labels row count mismatch in manifest for {timeframe}")
        quality = assess_label_quality_v9_6(labels, timeframe, dataset)
        physical_quality[timeframe] = quality
        errors.extend(quality["errors"])
    if manifest.get("quality") != physical_quality:
        errors.append("manifest quality mismatch")
    if report.get("quality") != physical_quality:
        errors.append("report quality mismatch")
    return _result(errors, warnings, manifest)


def validate_label_frame_v9_6(labels: pd.DataFrame, timeframe: str = "") -> list[str]:
    suffix = f" for {timeframe}" if timeframe else ""
    errors: list[str] = []
    if list(labels.columns) != REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6:
        errors.append(f"V9.6 label schema mismatch{suffix}")
    forbidden = [column for column in labels.columns if column.casefold() in FORBIDDEN_LABEL_COLUMNS_V9_6]
    if forbidden:
        errors.append(f"V9.6 forbidden label columns{suffix}: {forbidden}")
    if timeframe and len(labels) != EXPECTED_ROWS_V9_6[timeframe]:
        errors.append(f"V9.6 label rows mismatch{suffix}")
    if len(labels) and set(labels["target_name"].astype(str).unique()) != {TARGET_NAME_V9_6}:
        errors.append(f"V9.6 target_name mismatch{suffix}")
    if len(labels) and set(labels["label_schema_version"].astype(str).unique()) != {LABEL_SCHEMA_VERSION_V9_6}:
        errors.append(f"V9.6 label_schema_version mismatch{suffix}")
    if len(labels) and not (pd.to_datetime(labels["label_available_ts"], utc=True) > pd.to_datetime(labels["decision_ts"], utc=True)).all():
        errors.append(f"V9.6 label_available_ts must be after decision_ts{suffix}")
    if len(labels) and not labels["volatility_threshold_multiplier"].isin(PARAMETER_GRID_V9_6).all():
        errors.append(f"V9.6 unexpected volatility multiplier{suffix}")
    return errors


def validate_manifest_payload_v9_6(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION_V9_6:
        errors.append("V9.6 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V9.6 manifest status must be PASS")
    if manifest.get("decision") not in ALLOWED_DECISIONS_V9_6:
        errors.append("V9.6 decision is not allowed")
    if manifest.get("target_name") != TARGET_NAME_V9_6:
        errors.append("V9.6 target mismatch")
    if manifest.get("label_schema_version") != LABEL_SCHEMA_VERSION_V9_6:
        errors.append("V9.6 schema version mismatch")
    if manifest.get("label_columns") != REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6:
        errors.append("V9.6 label columns mismatch")
    if manifest.get("parameters_tested") != PARAMETER_GRID_V9_6:
        errors.append("V9.6 parameter grid mismatch")
    if manifest.get("findings") != FINDINGS_V9_6:
        errors.append("V9.6 findings mismatch")
    if manifest.get("safety") != SAFETY_FLAGS_V9_6:
        errors.append("V9.6 safety flags mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V9_6:
        errors.append("V9.6 limitations mismatch")
    if manifest.get("leakage_guard", {}).get("passed") is not True:
        errors.append("V9.6 leakage guard must pass")
    if set(manifest.get("outputs", {})) != set(TIMEFRAMES_V9_6):
        errors.append("V9.6 outputs timeframes mismatch")
    return errors


def validate_report_payload_v9_6(report: dict[str, Any]) -> list[str]:
    errors = validate_manifest_payload_v9_6(
        {
            "version": report.get("version"),
            "status": report.get("status"),
            "decision": report.get("decision"),
            "target_name": report.get("target_name"),
            "label_schema_version": LABEL_SCHEMA_VERSION_V9_6,
            "label_columns": REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6,
            "parameters_tested": report.get("parameters_tested"),
            "findings": report.get("findings"),
            "safety": report.get("safety"),
            "limitations": report.get("limitations"),
            "leakage_guard": report.get("leakage_guard"),
            "outputs": report.get("outputs", {}),
        }
    )
    if report.get("selected_volatility_threshold_multiplier") not in PARAMETER_GRID_V9_6:
        errors.append("V9.6 selected multiplier mismatch")
    if report.get("forbidden_output_scan", {}).get("passed") is not True:
        errors.append("V9.6 forbidden output scan must pass")
    return errors


def _validate_markdown(text: str) -> list[str]:
    lowered = text.casefold()
    errors = [f"markdown contains forbidden claim: {claim}" for claim in FORBIDDEN_CLAIMS_V9_6 if claim in lowered]
    for required in ["aucun backtest", "aucune strategie", "aucun signal actionnable", "aucun ordre", "aucun trading reel"]:
        if required not in lowered:
            errors.append(f"markdown missing required safety phrase: {required}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(errors: list[str], warnings: list[str], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION_V9_6, "passed": not errors, "errors": errors, "warnings": warnings, "manifest": manifest or {}}
