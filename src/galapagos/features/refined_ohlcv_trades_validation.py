from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.features.ohlcv_trades_feature_selection import is_forbidden_feature_v8_9
from galapagos.features.refined_ohlcv_trades_quality import assess_refined_ohlcv_trades_feature_quality_v9_0
from galapagos.features.refined_ohlcv_trades_schemas import (
    EXPECTED_LIMITATIONS_V9_0,
    EXPECTED_ROWS_V9_0,
    FEATURE_SELECTION_JSON_V8_9,
    MANIFEST_PATH_V9_0,
    REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0,
    REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0,
    REPORT_JSON_PATH_V9_0,
    REPORT_MD_PATH_V9_0,
    SAFETY_FLAGS_V9_0,
    TIMEFRAMES_V9_0,
    VERSION_V9_0,
)
from galapagos.validation.safety import validate_markdown_forbidden_claims


def validate_refined_ohlcv_trades_feature_store_v9_0(root: Path = Path(".")) -> dict[str, Any]:
    project_root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    for relative in [MANIFEST_PATH_V9_0, REPORT_JSON_PATH_V9_0, REPORT_MD_PATH_V9_0, FEATURE_SELECTION_JSON_V8_9]:
        if not (project_root / relative).exists():
            errors.append(f"missing V9.0 artifact: {relative}")
    if errors:
        return _result(errors, warnings)
    manifest = _read_json(project_root / MANIFEST_PATH_V9_0)
    report = _read_json(project_root / REPORT_JSON_PATH_V9_0)
    selection = _read_json(project_root / FEATURE_SELECTION_JSON_V8_9)
    errors.extend(validate_refined_feature_manifest_payload_v9_0(manifest, selection))
    if report != manifest:
        errors.append("V9.0 report JSON must match manifest")
    errors.extend(validate_markdown_forbidden_claims((project_root / REPORT_MD_PATH_V9_0).read_text(encoding="utf-8"), "V9.0 markdown"))
    for timeframe in TIMEFRAMES_V9_0:
        payload = manifest.get("outputs", {}).get(timeframe, {})
        output_path = project_root / payload.get("path", "")
        if not output_path.exists():
            errors.append(f"missing V9.0 refined features for {timeframe}: {payload.get('path')}")
            continue
        frame = read_parquet(output_path)
        if payload.get("sha256") != sha256_file(output_path):
            errors.append(f"V9.0 output checksum mismatch for {timeframe}")
        if payload.get("rows") != len(frame):
            errors.append(f"V9.0 manifest rows mismatch for {timeframe}")
        quality = assess_refined_ohlcv_trades_feature_quality_v9_0(
            frame,
            expected_rows=EXPECTED_ROWS_V9_0[timeframe],
            selected_features=REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0,
        )
        errors.extend(quality["errors"])
        if frame["source_feature_selection_sha256"].nunique() != 1:
            errors.append(f"V9.0 source_feature_selection_sha256 must be constant for {timeframe}")
    errors.extend(_forbidden_artifacts(project_root))
    return _result(errors, warnings, manifest)


def validate_refined_feature_manifest_payload_v9_0(manifest: dict[str, Any], selection: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION_V9_0:
        errors.append("V9.0 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V9.0 manifest status must be PASS")
    if manifest.get("feature_columns") != REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0:
        errors.append("V9.0 feature_columns mismatch")
    selected = manifest.get("selected_features", [])
    if selected != selection.get("candidate_refined_feature_set", {}).get("selected_features"):
        errors.append("V9.0 selected_features must match V8.9 selection")
    if manifest.get("selected_features_count") != len(selected) or len(selected) != 18:
        errors.append("V9.0 selected_features_count mismatch")
    forbidden = [feature for feature in selected if is_forbidden_feature_v8_9(feature)]
    if forbidden:
        errors.append(f"V9.0 selected features contain forbidden terms: {forbidden}")
    if manifest.get("safety") != SAFETY_FLAGS_V9_0:
        errors.append("V9.0 safety flags mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V9_0:
        errors.append("V9.0 limitations mismatch")
    if manifest.get("dropped_features_absent") is not True:
        errors.append("V9.0 dropped_features_absent must be true")
    return errors


def _forbidden_artifacts(root: Path) -> list[str]:
    forbidden = [
        Path("data/research/v9_0/labels"),
        Path("data/research/v9_0/datasets"),
        Path("data/research/v9_0/ml"),
        Path("data/research/v9_0/backtests"),
    ]
    return [f"forbidden V9.0 artifact exists: {path}" for path in forbidden if (root / path).exists()]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(errors: list[str], warnings: list[str], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"version": VERSION_V9_0, "passed": not errors, "errors": errors, "warnings": warnings, "manifest": manifest}
