from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.labels.horizon_event_label_redesign_v9_12_schemas import (
    ALLOWED_DECISIONS_V9_12,
    EXPECTED_ROWS_V9_12,
    FINDINGS_V9_12,
    FORBIDDEN_LABEL_COLUMNS_V9_12,
    HORIZON_EVENT_LABEL_COLUMNS_V9_12,
    MANIFEST_PATH_V9_12,
    REPORT_JSON_PATH_V9_12,
    REPORT_MD_PATH_V9_12,
    SAFETY_FLAGS_V9_12,
    SAFETY_V9_12,
    TIMEFRAMES_V9_12,
    VERSION_V9_12,
)


FORBIDDEN_CLAIMS_V9_12 = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "profitability confirmed",
]
FORBIDDEN_NAMES_V9_12 = {".DS_Store", ".env", "Icon", "Icon\r"}
FORBIDDEN_SUFFIXES_V9_12 = {
    ".pyc",
    ".pkl",
    ".pickle",
    ".joblib",
    ".onnx",
    ".pt",
    ".pth",
    ".ckpt",
    ".pem",
    ".key",
    ".sha256.json",
    ".sha256.txt",
}


def validate_horizon_event_label_redesign_v9_12(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH_V9_12
    manifest_path = root / MANIFEST_PATH_V9_12
    markdown_path = root / REPORT_MD_PATH_V9_12
    for path, label in [(report_path, "report"), (manifest_path, "manifest"), (markdown_path, "markdown")]:
        if not path.exists():
            errors.append(f"missing V9.12 {label}: {path.relative_to(root)}")
    if errors:
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_12(report))
    errors.extend(validate_manifest_payload_v9_12(manifest, report))
    errors.extend(validate_markdown_v9_12(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_label_outputs_v9_12(root, report))
    errors.extend(validate_no_forbidden_artifacts_v9_12(root))
    return errors


def validate_report_payload_v9_12(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION_V9_12:
        errors.append("V9.12 report version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.12 report status must be PASS")
    decision = report.get("v9_12_decision", {}).get("decision")
    if decision not in ALLOWED_DECISIONS_V9_12:
        errors.append("V9.12 decision is not allowed")
    if report.get("full_data_available") is not True:
        errors.append("V9.12 full_data_available must be true for a produced candidate")
    recommended = report.get("recommended_candidate", {})
    if recommended.get("target_name") != "up_down_flat_volnorm_h4":
        errors.append("V9.12 recommended candidate must be up_down_flat_volnorm_h4")
    if recommended.get("multiplier") != 1.25:
        errors.append("V9.12 recommended multiplier must be 1.25")
    if not report.get("designs_tested", {}).get("horizon_extension"):
        errors.append("V9.12 must include horizon extension design audit")
    if not report.get("designs_tested", {}).get("event_based_diagnostic"):
        errors.append("V9.12 must include event-based diagnostic audit")
    if not report.get("comparison_with_v9_6"):
        errors.append("V9.12 must compare with V9.6")
    if report.get("leakage_guard", {}).get("passed") is not True:
        errors.append("V9.12 leakage guard must pass")
    if report.get("event_based_safety_guard", {}).get("passed") is not True:
        errors.append("V9.12 event-based safety guard must pass")
    if report.get("forbidden_output_scan", {}).get("passed") is not True:
        errors.append("V9.12 forbidden output scan must pass")
    if report.get("findings") != FINDINGS_V9_12:
        errors.append("V9.12 findings mismatch")
    if report.get("safety") != SAFETY_V9_12:
        errors.append("V9.12 safety mismatch")
    if report.get("safety_flags") != SAFETY_FLAGS_V9_12:
        errors.append("V9.12 safety flags mismatch")
    errors.extend(_reject_hash_or_sidecar_fields(report, "report"))
    return errors


def validate_manifest_payload_v9_12(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION_V9_12:
        errors.append("V9.12 manifest version mismatch")
    if manifest.get("status") != report.get("status"):
        errors.append("V9.12 manifest status mismatch")
    if manifest.get("label_columns") != HORIZON_EVENT_LABEL_COLUMNS_V9_12:
        errors.append("V9.12 manifest schema mismatch")
    if manifest.get("v9_12_decision", {}).get("decision") != report.get("v9_12_decision", {}).get("decision"):
        errors.append("V9.12 manifest decision mismatch")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.12 manifest findings mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.12 manifest safety flags mismatch")
    errors.extend(_reject_hash_or_sidecar_fields(manifest, "manifest"))
    return errors


def validate_label_outputs_v9_12(root: Path, report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    outputs = report.get("outputs", {})
    for timeframe in TIMEFRAMES_V9_12:
        output = outputs.get(timeframe, {})
        path = root / output.get("path", "")
        if not path.is_file():
            errors.append(f"missing V9.12 labels output for {timeframe}: {path}")
            continue
        frame = pd.read_parquet(path, engine="pyarrow")
        if list(frame.columns) != HORIZON_EVENT_LABEL_COLUMNS_V9_12:
            errors.append(f"V9.12 labels schema mismatch for {timeframe}")
        if len(frame) != EXPECTED_ROWS_V9_12[timeframe]:
            errors.append(f"V9.12 row count mismatch for {timeframe}")
        forbidden = [column for column in frame.columns if column.casefold() in FORBIDDEN_LABEL_COLUMNS_V9_12]
        if forbidden:
            errors.append(f"V9.12 forbidden columns present for {timeframe}: {forbidden}")
        available = pd.to_datetime(frame["label_available_ts"], utc=True)
        decision = pd.to_datetime(frame["decision_ts"], utc=True)
        valid_available = available.notna()
        if not (available[valid_available] > decision[valid_available]).all():
            errors.append(f"V9.12 label_available_ts must be after decision_ts for {timeframe}")
        if frame["target_name"].dropna().nunique() != 1 or frame["target_name"].dropna().iloc[0] != "up_down_flat_volnorm_h4":
            errors.append(f"V9.12 target_name mismatch for {timeframe}")
    return errors


def validate_markdown_v9_12(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS_V9_12:
        if claim in lowered:
            errors.append(f"V9.12 markdown contains forbidden claim: {claim}")
    for phrase in [
        "aucun backtest",
        "aucun trading",
        "aucun ordre",
        "aucune strategie",
        "aucun signal actionnable",
        "aucun sidecar",
        "aucune empreinte zip",
    ]:
        if phrase not in lowered:
            errors.append(f"V9.12 markdown missing safety phrase: {phrase}")
    return errors


def validate_no_forbidden_artifacts_v9_12(root: Path) -> list[str]:
    errors: list[str] = []
    forbidden_roots = [
        root / "data/research/v9_12/datasets",
        root / "data/research/v9_12/ml",
        root / "data/research/v9_12/backtests",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models",
        root / "checkpoints",
    ]
    for path in forbidden_roots:
        if path.exists():
            errors.append(f"forbidden V9.12 artifact exists: {path}")
    for path in root.glob("projet-galapagos-v9.12-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.12 sidecar present: {path}")
    for path in [root / "Icon", root / "Icon\r"]:
        if path.exists():
            errors.append(f"forbidden parasite file present: {path}")
    return errors


def _reject_hash_or_sidecar_fields(payload: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key).casefold()
            if key_text == "zip_sha256" or key_text.startswith("sidecar_"):
                errors.append(f"{path} contains forbidden hash or sidecar field: {key}")
            errors.extend(_reject_hash_or_sidecar_fields(value, f"{path}.{key}"))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            errors.extend(_reject_hash_or_sidecar_fields(item, f"{path}[{index}]"))
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
