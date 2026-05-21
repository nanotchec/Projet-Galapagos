from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pandas.testing as pdt

from galapagos.data.public_market.multi_day import output_path as v2_9_ohlcv_path
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.labels.forward_returns import build_forward_labels
from galapagos.labels.multi_day_config import (
    EXPECTED_LIMITATIONS_V3_1,
    LABEL_SCHEMA_VERSION,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    TIMEFRAMES_V3_1,
    VERSION,
    output_path,
)
from galapagos.labels.multi_day_quality import assess_multi_day_label_quality
from galapagos.labels.registry import HORIZONS, THRESHOLD
from galapagos.labels.schemas import FORBIDDEN_COLUMNS_V3_1, LABEL_COLUMNS_V3_1
from galapagos.validation.manifests import load_json
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


RUN_ID_PATTERN = re.compile(r"^v3_1_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "label_run_id",
    "input_ohlcv",
    "outputs",
    "label_schema_version",
    "label_columns",
    "horizons",
    "threshold",
    "quality",
    "safety",
    "limitations",
}
REPORT_KEYS = MANIFEST_KEYS.copy()
INPUT_KEYS = {"path", "sha256", "rows"}
OUTPUT_KEYS = {"path", "sha256", "bytes", "rows", "format"}
QUALITY_KEYS = {
    "rows",
    "expected_rows",
    "duplicate_rows",
    "tail_rows",
    "valid_counts_by_horizon",
    "null_counts_by_column",
    "forbidden_columns_present",
    "timestamps_utc",
    "monotonic_event_ts",
    "label_available_ts_valid",
    "label_end_ts_valid",
    "causal_separation_guard_passed",
    "source_hashes_valid",
    "errors",
    "warnings",
}
SAFETY_KEYS = {
    "public_read_only",
    "authentication_used",
    "api_key_used",
    "private_endpoint_used",
    "orders_enabled",
    "paper_live_enabled",
    "trading_enabled",
    "ml_enabled",
    "labels_enabled",
    "dataset_enabled",
    "backtest_enabled",
    "strategy_enabled",
    "execution_enabled",
}
FORBIDDEN_ARTIFACT_PREFIXES = [
    "data/research/v3_1/datasets",
    "data/research/v3_1/ml",
    "data/research/v3_1/backtests",
    "reports/strategies",
    "reports/signals",
    "reports/predictions",
    "orders",
    "execution",
]


def validate_multi_day_label_factory_v3_1(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    manifest_path = root / MANIFEST_PATH
    report_path = root / REPORT_JSON_PATH
    if not manifest_path.exists():
        return _result([f"missing V3.1 manifest: {MANIFEST_PATH}"])
    if not report_path.exists():
        return _result([f"missing V3.1 label report: {REPORT_JSON_PATH}"])
    manifest = load_json(manifest_path)
    report = load_json(report_path)
    errors.extend(_validate_manifest_structure(root, manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V3.1 manifest"))

    physical_quality: dict[str, dict[str, Any]] = {}
    for timeframe in TIMEFRAMES_V3_1:
        input_path = v2_9_ohlcv_path(root, timeframe)
        output = output_path(root, timeframe)
        if not input_path.exists():
            errors.append(f"missing V3.1 input OHLCV: {input_path.relative_to(root)}")
            continue
        if not output.exists():
            errors.append(f"missing V3.1 output labels: {output.relative_to(root)}")
            continue
        frame = read_parquet(output)
        input_frame = read_parquet(input_path)
        errors.extend(_validate_input_entry(root, manifest, timeframe, input_path, input_frame))
        errors.extend(_validate_output_entry(root, manifest, timeframe, output, frame))
        frame_errors, quality = _validate_label_frame(timeframe, frame, input_path, input_frame, manifest.get("label_run_id"))
        errors.extend(frame_errors)
        physical_quality[timeframe] = quality
    errors.extend(_validate_manifest_quality(manifest, physical_quality))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V3.1 label report"))
    errors.extend(_validate_markdown(root))
    errors.extend(_find_forbidden_v3_1_artifacts(root))
    return _result(errors, manifest=manifest)


def _validate_manifest_structure(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V3.1 manifest"))
    if manifest.get("version") != VERSION:
        errors.append("V3.1 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V3.1 manifest status must be PASS")
    if not isinstance(manifest.get("created_at_utc"), str) or not manifest["created_at_utc"].endswith("Z"):
        errors.append("V3.1 manifest created_at_utc invalid")
    run_id = manifest.get("label_run_id")
    if not isinstance(run_id, str) or RUN_ID_PATTERN.fullmatch(run_id) is None:
        errors.append("V3.1 manifest label_run_id invalid")
    if manifest.get("label_schema_version") != LABEL_SCHEMA_VERSION:
        errors.append("V3.1 manifest label_schema_version mismatch")
    if manifest.get("label_columns") != LABEL_COLUMNS_V3_1:
        errors.append("V3.1 manifest label_columns mismatch")
    if manifest.get("horizons") != HORIZONS:
        errors.append("V3.1 manifest horizons mismatch")
    if manifest.get("threshold") != THRESHOLD:
        errors.append("V3.1 manifest threshold mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V3_1:
        errors.append("V3.1 manifest limitations mismatch")
    for section, keys in [("input_ohlcv", INPUT_KEYS), ("outputs", OUTPUT_KEYS), ("quality", QUALITY_KEYS)]:
        payload = manifest.get(section, {})
        errors.extend(validate_exact_keys(payload, set(TIMEFRAMES_V3_1), f"V3.1 manifest {section}"))
        for timeframe, block in payload.items():
            errors.extend(validate_exact_keys(block, keys, f"V3.1 manifest {section}.{timeframe}"))
    errors.extend(validate_exact_keys(manifest.get("safety"), SAFETY_KEYS, "V3.1 manifest safety"))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    for timeframe in TIMEFRAMES_V3_1:
        input_path = v2_9_ohlcv_path(root, timeframe)
        output = output_path(root, timeframe)
        input_payload = manifest.get("input_ohlcv", {}).get(timeframe, {})
        output_payload = manifest.get("outputs", {}).get(timeframe, {})
        if input_payload.get("path") != str(input_path.relative_to(root)):
            errors.append(f"V3.1 manifest input path mismatch for {timeframe}")
        if output_payload.get("path") != str(output.relative_to(root)):
            errors.append(f"V3.1 manifest output path mismatch for {timeframe}")
    return errors


def _validate_safety(safety: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if safety.get("public_read_only") is not True:
        errors.append("V3.1 safety flag public_read_only must be True")
    if safety.get("labels_enabled") is not True:
        errors.append("V3.1 safety flag labels_enabled must be True")
    for flag in sorted(SAFETY_KEYS - {"public_read_only", "labels_enabled"}):
        if safety.get(flag) is not False:
            errors.append(f"V3.1 safety flag {flag} must be False")
    return errors


def _validate_input_entry(root: Path, manifest: dict[str, Any], timeframe: str, path: Path, frame: pd.DataFrame) -> list[str]:
    payload = manifest.get("input_ohlcv", {}).get(timeframe, {})
    expected = {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "rows": int(len(frame)),
    }
    return [f"V3.1 manifest input mismatch for {timeframe}.{field}" for field, value in expected.items() if payload.get(field) != value]


def _validate_output_entry(root: Path, manifest: dict[str, Any], timeframe: str, path: Path, frame: pd.DataFrame) -> list[str]:
    payload = manifest.get("outputs", {}).get(timeframe, {})
    expected = {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(len(frame)),
        "format": "parquet",
    }
    return [f"V3.1 manifest output mismatch for {timeframe}.{field}" for field, value in expected.items() if payload.get(field) != value]


def _validate_label_frame(
    timeframe: str,
    frame: pd.DataFrame,
    input_path: Path,
    input_frame: pd.DataFrame,
    label_run_id: Any,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if list(frame.columns) != LABEL_COLUMNS_V3_1:
        errors.append(f"V3.1 label schema mismatch for {timeframe}")
    forbidden = _forbidden_columns(frame)
    if forbidden:
        errors.append(f"V3.1 forbidden label columns for {timeframe}: {forbidden}")
    if len(frame) != len(input_frame):
        errors.append(f"V3.1 label row count mismatch for {timeframe}")
    input_sha = sha256_file(input_path)
    source_hashes_valid = bool("source_ohlcv_sha256" in frame.columns and set(frame["source_ohlcv_sha256"].astype(str).unique()) == {input_sha})
    if not source_hashes_valid:
        errors.append(f"V3.1 source_ohlcv_sha256 mismatch for {timeframe}")
    if "label_run_id" in frame.columns and label_run_id is not None:
        if set(frame["label_run_id"].astype(str).unique()) != {str(label_run_id)}:
            errors.append(f"V3.1 label_run_id mismatch for {timeframe}")
    if "label_schema_version" in frame.columns:
        if set(frame["label_schema_version"].astype(str).unique()) != {LABEL_SCHEMA_VERSION}:
            errors.append(f"V3.1 label_schema_version mismatch for {timeframe}")
    expected = build_forward_labels(
        input_frame,
        input_sha,
        str(label_run_id),
        label_schema_version=LABEL_SCHEMA_VERSION,
    )
    errors.extend(_compare_recomputed_labels(timeframe, frame, expected))
    errors.extend(_validate_temporal_label_rules(timeframe, frame))
    quality = assess_multi_day_label_quality(frame, timeframe)
    quality["source_hashes_valid"] = source_hashes_valid
    errors.extend(f"V3.1 physical quality error for {timeframe}: {error}" for error in quality["errors"])
    return errors, quality


def _compare_recomputed_labels(timeframe: str, frame: pd.DataFrame, expected: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if list(frame.columns) != LABEL_COLUMNS_V3_1:
        return errors
    comparable = LABEL_COLUMNS_V3_1
    try:
        pdt.assert_frame_equal(
            frame[comparable].reset_index(drop=True),
            expected[comparable].reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            rtol=1e-12,
            atol=1e-12,
        )
    except AssertionError as exc:
        text = str(exc)
        if "future_close_h1" in text:
            errors.append(f"V3.1 future_close_h1 mismatch for {timeframe}")
        elif "future_log_return_h3" in text:
            errors.append(f"V3.1 future_log_return_h3 mismatch for {timeframe}")
        elif "direction_h5" in text:
            errors.append(f"V3.1 direction_h5 mismatch for {timeframe}")
        elif "up_down_flat_h1" in text:
            errors.append(f"V3.1 up_down_flat_h1 mismatch for {timeframe}")
        elif "label_valid" in text or "tail_row" in text:
            errors.append(f"V3.1 label_valid or tail_row mismatch for {timeframe}")
        else:
            errors.append(f"V3.1 recomputed labels mismatch for {timeframe}: {text.splitlines()[0]}")
    return errors


def _validate_temporal_label_rules(timeframe: str, frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    valid_any = frame[[f"label_valid_h{h}" for h in HORIZONS]].any(axis=1)
    if valid_any.any():
        label_available = pd.to_datetime(frame.loc[valid_any, "label_available_ts"], utc=True)
        decision = pd.to_datetime(frame.loc[valid_any, "decision_ts"], utc=True)
        if (label_available <= decision).any():
            errors.append(f"V3.1 label_available_ts <= decision_ts for valid labels in {timeframe}")
    for h in HORIZONS:
        valid = frame[f"label_valid_h{h}"]
        if (valid & frame[f"future_close_h{h}"].isna()).any():
            errors.append(f"V3.1 label_valid_h{h} true with null future_close in {timeframe}")
        if (valid & frame[f"label_end_ts_h{h}"].isna()).any():
            errors.append(f"V3.1 label_valid_h{h} true with null label_end_ts in {timeframe}")
        expected_tail_valid = [True] * max(0, len(frame) - h) + [False] * min(h, len(frame))
        if list(valid.astype(bool)) != expected_tail_valid:
            errors.append(f"V3.1 label_valid_h{h} tail mismatch for {timeframe}")
    expected_tail = ~(frame["label_valid_h1"] & frame["label_valid_h3"] & frame["label_valid_h5"])
    if not (frame["tail_row"].astype(bool).reset_index(drop=True) == expected_tail.reset_index(drop=True)).all():
        errors.append(f"V3.1 tail_row mismatch for {timeframe}")
    return errors


def _forbidden_columns(frame: pd.DataFrame) -> list[str]:
    forbidden: list[str] = []
    for column in frame.columns:
        if column in LABEL_COLUMNS_V3_1:
            continue
        lower = str(column).casefold()
        if any(term in lower for term in FORBIDDEN_COLUMNS_V3_1):
            forbidden.append(str(column))
    return sorted(forbidden)


def _validate_manifest_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe in TIMEFRAMES_V3_1:
        declared = manifest.get("quality", {}).get(timeframe)
        physical = physical_quality.get(timeframe)
        if not isinstance(declared, dict):
            errors.append(f"V3.1 manifest quality missing for {timeframe}")
            continue
        if not isinstance(physical, dict):
            errors.append(f"V3.1 physical quality unavailable for {timeframe}")
            continue
        for field in sorted(QUALITY_KEYS - {"warnings", "errors"}):
            if declared.get(field) != physical.get(field):
                errors.append(f"V3.1 manifest quality mismatch for {timeframe}.{field}")
        if declared.get("errors") != physical.get("errors"):
            errors.append(f"V3.1 manifest quality errors mismatch for {timeframe}")
        if declared.get("warnings") != physical.get("warnings"):
            errors.append(f"V3.1 manifest quality warnings mismatch for {timeframe}")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(report, REPORT_KEYS, "V3.1 label report"))
    expected = {key: manifest.get(key) for key in REPORT_KEYS}
    for field, value in expected.items():
        if report.get(field) != value:
            errors.append(f"V3.1 label report {field} mismatch")
    errors.extend(_validate_safety(report.get("safety", {})))
    return errors


def _validate_markdown(root: Path) -> list[str]:
    path = root / REPORT_MD_PATH
    if not path.exists():
        return [f"missing V3.1 label markdown: {REPORT_MD_PATH}"]
    text = path.read_text(encoding="utf-8")
    errors = validate_markdown_forbidden_claims(text, "V3.1 label markdown")
    required = [
        "V3.1 ne valide aucune stratégie",
        "V3.1 ne produit aucun dataset ML",
        "V3.1 ne produit aucun modèle ML",
        "V3.1 ne produit aucun backtest",
        "V3.1 ne produit aucun signal de trading",
        "V3.1 ne produit aucun ordre",
        "V3.1 n’autorise aucun paper live",
        "V3.1 n’autorise aucun trading réel",
    ]
    normalized_text = text.replace("’", "'")
    for clause in required:
        if clause.replace("’", "'") not in normalized_text:
            errors.append(f"V3.1 label markdown missing safety clause: {clause}")
    return errors


def _find_forbidden_v3_1_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    feature_root = root / "data/research/v3_0/features"
    if feature_root.exists():
        for child in sorted(feature_root.rglob("*")):
            if child.is_file() and child.suffix == ".parquet":
                try:
                    frame = read_parquet(child)
                except Exception:
                    continue
                leaked = [column for column in frame.columns if str(column).casefold().startswith(("future_", "label_"))]
                if leaked:
                    errors.append(f"Forbidden V3.1 label leakage in V3.0 features: {child.relative_to(root)}")
    for prefix in FORBIDDEN_ARTIFACT_PREFIXES:
        path = root / prefix
        if path.exists():
            if path.is_file():
                errors.append(f"Forbidden V3.1 artifact detected: {path.relative_to(root)}")
            else:
                children = sorted(child for child in path.rglob("*") if child.is_file())
                if children:
                    errors.extend(f"Forbidden V3.1 artifact detected: {child.relative_to(root)}" for child in children[:20])
                else:
                    errors.append(f"Forbidden V3.1 artifact detected: {path.relative_to(root)}")
    backtests = root / "reports/backtests"
    if backtests.exists():
        for child in sorted(backtests.rglob("*")):
            if not child.is_file() or child.name == ".gitkeep":
                continue
            if _is_legacy_backtest_report(child.relative_to(root)):
                continue
            errors.append(f"Forbidden V3.1 artifact detected: {child.relative_to(root)}")
    return errors


def _is_legacy_backtest_report(relative: Path) -> bool:
    if len(relative.parts) != 3 or relative.parts[0] != "reports" or relative.parts[1] != "backtests":
        return False
    name = relative.parts[2]
    legacy_prefixes = (
        "baseline_suite_v1_",
        "codex_cli_sample_backtest_v1_",
        "codex_prompt_mode_comparison_v1_",
        "codex_setup_review_v1_",
        "first_mechanical_backtest_review.",
        "llm_offline_suite_v1_",
        "mechanical_backtest_v1_",
    )
    if name.startswith(legacy_prefixes):
        return True
    return bool(re.fullmatch(r"backtest_[0-9a-f-]{36}\.(json|md)", name))


def _isclose_or_both_nan(left: pd.Series, right: pd.Series) -> pd.Series:
    return pd.Series(np.isclose(left, right, equal_nan=True), index=left.index)


def _result(errors: list[str], **extra: Any) -> dict[str, Any]:
    return {"passed": not errors, "errors": errors, **extra}
