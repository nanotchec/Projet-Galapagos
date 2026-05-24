from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import pandas.testing as pdt

from galapagos.data.public_market.max_history_window import MANIFEST_PATH_V5_0
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.labels.forward_returns import build_forward_labels
from galapagos.labels.max_history_window import (
    EXPECTED_LIMITATIONS_V5_2,
    LABEL_SCHEMA_VERSION_V5_2,
    MANIFEST_PATH_V5_2,
    REPORT_JSON_PATH_V5_2,
    REPORT_MD_PATH_V5_2,
    TIMEFRAMES_V5_2,
    VERSION_V5_2,
    input_ohlcv_path,
    load_v5_0_ohlcv_manifest,
    output_path,
)
from galapagos.labels.max_history_window_quality import assess_max_history_label_quality
from galapagos.labels.registry import HORIZONS, THRESHOLD
from galapagos.labels.schemas import FORBIDDEN_COLUMNS_V5_2, LABEL_COLUMNS_V5_2
from galapagos.validation.manifests import load_json
from galapagos.validation.safety import (
    scan_payload_for_forbidden_claims,
    validate_exact_keys,
    validate_markdown_forbidden_claims,
)


RUN_ID_PATTERN_V5_2 = re.compile(r"^v5_2_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
FEATURE_MANIFEST_PATH_V5_1 = Path("reports/manifests/max_history_causal_feature_store_v5_1_manifest.json")
MANIFEST_KEYS = {
    "version",
    "status",
    "created_at_utc",
    "label_run_id",
    "input_ohlcv_manifest",
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
INPUT_MANIFEST_KEYS = {"path", "sha256", "window_start", "window_end", "total_days"}
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
FORBIDDEN_V5_2_PATHS = [
    "data/research/v5_2/datasets",
    "data/research/v5_2/ml",
    "data/research/v5_2/backtests",
    "data/research/v5_2/strategies",
    "reports/backtests",
    "reports/strategies",
    "reports/signals",
    "reports/predictions",
    "orders",
    "execution",
    "models",
    "checkpoints",
]
FORBIDDEN_MODEL_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
IGNORED_SCAN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}


def validate_max_history_label_factory_v5_2(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    manifest_path = root / MANIFEST_PATH_V5_2
    report_path = root / REPORT_JSON_PATH_V5_2
    if not manifest_path.exists():
        return _result([f"missing V5.2 manifest: {MANIFEST_PATH_V5_2}"])
    if not report_path.exists():
        return _result([f"missing V5.2 label report: {REPORT_JSON_PATH_V5_2}"])

    v5_0_manifest = load_v5_0_ohlcv_manifest(root)
    manifest = load_json(manifest_path)
    report = load_json(report_path)
    errors.extend(_validate_manifest_structure(root, manifest, v5_0_manifest))
    errors.extend(scan_payload_for_forbidden_claims(manifest, "V5.2 manifest"))

    physical_quality: dict[str, dict[str, Any]] = {}
    for timeframe in TIMEFRAMES_V5_2:
        input_path = input_ohlcv_path(root, timeframe, v5_0_manifest)
        label_path = output_path(
            root,
            timeframe,
            v5_0_manifest["discovery"]["window_start"],
            v5_0_manifest["discovery"]["window_end"],
        )
        if not input_path.exists():
            errors.append(f"missing V5.2 input OHLCV: {input_path.relative_to(root)}")
            continue
        if not label_path.exists():
            errors.append(f"missing V5.2 output labels: {label_path.relative_to(root)}")
            continue
        input_frame = read_parquet(input_path)
        label_frame = read_parquet(label_path)
        errors.extend(_validate_input_entry(root, manifest, timeframe, input_path, input_frame))
        errors.extend(_validate_output_entry(root, manifest, timeframe, label_path, label_frame))
        frame_errors, quality = _validate_label_frame(
            timeframe,
            label_frame,
            input_path,
            input_frame,
            manifest.get("label_run_id"),
            expected_rows=int(v5_0_manifest["expected_rows"][timeframe]),
        )
        errors.extend(frame_errors)
        physical_quality[timeframe] = quality

    errors.extend(_validate_manifest_quality(manifest, physical_quality))
    errors.extend(_validate_report(manifest, report))
    errors.extend(scan_payload_for_forbidden_claims(report, "V5.2 label report"))
    errors.extend(_validate_markdown(root))
    errors.extend(_validate_v5_1_features_unchanged(root))
    errors.extend(_find_forbidden_v5_2_artifacts(root))
    return _result(errors, manifest=manifest)


def _validate_manifest_structure(root: Path, manifest: dict[str, Any], v5_0_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(manifest, MANIFEST_KEYS, "V5.2 manifest"))
    if manifest.get("version") != VERSION_V5_2:
        errors.append("V5.2 manifest version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V5.2 manifest status must be PASS")
    if not isinstance(manifest.get("created_at_utc"), str) or not manifest["created_at_utc"].endswith("Z"):
        errors.append("V5.2 manifest created_at_utc invalid")
    run_id = manifest.get("label_run_id")
    if not isinstance(run_id, str) or RUN_ID_PATTERN_V5_2.fullmatch(run_id) is None:
        errors.append("V5.2 manifest label_run_id invalid")
    if manifest.get("label_schema_version") != LABEL_SCHEMA_VERSION_V5_2:
        errors.append("V5.2 manifest label_schema_version mismatch")
    if manifest.get("label_columns") != LABEL_COLUMNS_V5_2:
        errors.append("V5.2 manifest label_columns mismatch")
    if manifest.get("horizons") != HORIZONS:
        errors.append("V5.2 manifest horizons mismatch")
    if manifest.get("threshold") != THRESHOLD:
        errors.append("V5.2 manifest threshold mismatch")
    if manifest.get("limitations") != EXPECTED_LIMITATIONS_V5_2:
        errors.append("V5.2 manifest limitations mismatch")

    errors.extend(
        validate_exact_keys(
            manifest.get("input_ohlcv_manifest"),
            INPUT_MANIFEST_KEYS,
            "V5.2 manifest input_ohlcv_manifest",
        )
    )
    expected_input_manifest = {
        "path": MANIFEST_PATH_V5_0.as_posix(),
        "sha256": sha256_file(root / MANIFEST_PATH_V5_0),
        "window_start": v5_0_manifest["discovery"]["window_start"],
        "window_end": v5_0_manifest["discovery"]["window_end"],
        "total_days": v5_0_manifest["discovery"]["total_days"],
    }
    if manifest.get("input_ohlcv_manifest") != expected_input_manifest:
        errors.append("V5.2 input_ohlcv_manifest mismatch")

    for section, keys in [("input_ohlcv", INPUT_KEYS), ("outputs", OUTPUT_KEYS), ("quality", QUALITY_KEYS)]:
        payload = manifest.get(section, {})
        errors.extend(validate_exact_keys(payload, set(TIMEFRAMES_V5_2), f"V5.2 manifest {section}"))
        for timeframe, block in payload.items():
            errors.extend(validate_exact_keys(block, keys, f"V5.2 manifest {section}.{timeframe}"))
    errors.extend(validate_exact_keys(manifest.get("safety"), SAFETY_KEYS, "V5.2 manifest safety"))
    errors.extend(_validate_safety(manifest.get("safety", {})))
    for timeframe in TIMEFRAMES_V5_2:
        input_path = input_ohlcv_path(root, timeframe, v5_0_manifest)
        label_path = output_path(
            root,
            timeframe,
            v5_0_manifest["discovery"]["window_start"],
            v5_0_manifest["discovery"]["window_end"],
        )
        if manifest.get("input_ohlcv", {}).get(timeframe, {}).get("path") != str(input_path.relative_to(root)):
            errors.append(f"V5.2 manifest input path mismatch for {timeframe}")
        if manifest.get("outputs", {}).get(timeframe, {}).get("path") != str(label_path.relative_to(root)):
            errors.append(f"V5.2 manifest output path mismatch for {timeframe}")
    return errors


def _validate_safety(safety: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if safety.get("public_read_only") is not True:
        errors.append("V5.2 safety flag public_read_only must be True")
    if safety.get("labels_enabled") is not True:
        errors.append("V5.2 safety flag labels_enabled must be True")
    for flag in sorted(SAFETY_KEYS - {"public_read_only", "labels_enabled"}):
        if safety.get(flag) is not False:
            errors.append(f"V5.2 safety flag {flag} must be False")
    return errors


def _validate_input_entry(root: Path, manifest: dict[str, Any], timeframe: str, path: Path, frame: pd.DataFrame) -> list[str]:
    payload = manifest.get("input_ohlcv", {}).get(timeframe, {})
    expected = {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "rows": int(len(frame)),
    }
    return [f"V5.2 manifest input mismatch for {timeframe}.{field}" for field, value in expected.items() if payload.get(field) != value]


def _validate_output_entry(root: Path, manifest: dict[str, Any], timeframe: str, path: Path, frame: pd.DataFrame) -> list[str]:
    payload = manifest.get("outputs", {}).get(timeframe, {})
    expected = {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(len(frame)),
        "format": "parquet",
    }
    return [f"V5.2 manifest output mismatch for {timeframe}.{field}" for field, value in expected.items() if payload.get(field) != value]


def _validate_label_frame(
    timeframe: str,
    frame: pd.DataFrame,
    input_path: Path,
    input_frame: pd.DataFrame,
    label_run_id: Any,
    *,
    expected_rows: int,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    errors.extend(_validate_label_schema(frame, timeframe))
    if len(frame) != len(input_frame):
        errors.append(f"V5.2 label row count mismatch for {timeframe}")
    input_sha = sha256_file(input_path)
    errors.extend(_validate_label_metadata(timeframe, frame, str(label_run_id), input_sha))
    errors.extend(
        _validate_label_values_against_ohlcv(
            timeframe,
            frame,
            input_frame,
            str(label_run_id),
            source_ohlcv_sha256=input_sha,
        )
    )
    source_hashes_valid = _source_hashes_valid(frame, input_sha)
    quality = assess_max_history_label_quality(frame, expected_rows=expected_rows)
    quality["source_hashes_valid"] = source_hashes_valid
    errors.extend(f"V5.2 physical quality error for {timeframe}: {error}" for error in quality["errors"])
    return errors, quality


def _validate_label_schema(frame: pd.DataFrame, timeframe: str) -> list[str]:
    errors: list[str] = []
    if list(frame.columns) != LABEL_COLUMNS_V5_2:
        errors.append(f"V5.2 label schema mismatch for {timeframe}")
    forbidden = _forbidden_columns(frame)
    if forbidden:
        errors.append(f"V5.2 forbidden label columns for {timeframe}: {forbidden}")
    return errors


def _validate_label_metadata(timeframe: str, frame: pd.DataFrame, label_run_id: str, source_ohlcv_sha256: str) -> list[str]:
    errors: list[str] = []
    if not _source_hashes_valid(frame, source_ohlcv_sha256):
        errors.append(f"V5.2 source_ohlcv_sha256 mismatch for {timeframe}")
    if "label_run_id" in frame.columns and set(frame["label_run_id"].astype(str).unique()) != {str(label_run_id)}:
        errors.append(f"V5.2 label_run_id mismatch for {timeframe}")
    if "label_schema_version" in frame.columns:
        if set(frame["label_schema_version"].astype(str).unique()) != {LABEL_SCHEMA_VERSION_V5_2}:
            errors.append(f"V5.2 label_schema_version mismatch for {timeframe}")
    return errors


def _source_hashes_valid(frame: pd.DataFrame, source_ohlcv_sha256: str) -> bool:
    return bool(
        "source_ohlcv_sha256" in frame.columns
        and set(frame["source_ohlcv_sha256"].astype(str).unique()) == {source_ohlcv_sha256}
    )


def _validate_label_values_against_ohlcv(
    timeframe: str,
    label_frame: pd.DataFrame,
    input_frame: pd.DataFrame,
    label_run_id: str,
    *,
    source_ohlcv_sha256: str,
) -> list[str]:
    if list(label_frame.columns) != LABEL_COLUMNS_V5_2:
        return []
    expected = build_forward_labels(
        input_frame,
        source_ohlcv_sha256,
        label_run_id,
        label_schema_version=LABEL_SCHEMA_VERSION_V5_2,
    )
    errors = _compare_recomputed_labels(timeframe, label_frame, expected)
    errors.extend(_validate_temporal_label_rules(timeframe, label_frame))
    return errors


def _compare_recomputed_labels(timeframe: str, frame: pd.DataFrame, expected: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    try:
        pdt.assert_frame_equal(
            frame[LABEL_COLUMNS_V5_2].reset_index(drop=True),
            expected[LABEL_COLUMNS_V5_2].reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            rtol=1e-12,
            atol=1e-12,
        )
    except AssertionError as exc:
        text = str(exc)
        if "future_close_h1" in text:
            errors.append(f"V5.2 future_close_h1 mismatch for {timeframe}")
        elif "future_log_return_h3" in text:
            errors.append(f"V5.2 future_log_return_h3 mismatch for {timeframe}")
        elif "direction_h5" in text:
            errors.append(f"V5.2 direction_h5 mismatch for {timeframe}")
        elif "up_down_flat_h1" in text:
            errors.append(f"V5.2 up_down_flat_h1 mismatch for {timeframe}")
        elif "label_valid" in text or "tail_row" in text:
            errors.append(f"V5.2 label_valid or tail_row mismatch for {timeframe}")
        else:
            errors.append(f"V5.2 recomputed labels mismatch for {timeframe}: {text.splitlines()[0]}")
    return errors


def _validate_temporal_label_rules(timeframe: str, frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    valid_any = frame[[f"label_valid_h{h}" for h in HORIZONS]].any(axis=1)
    if valid_any.any():
        label_available = pd.to_datetime(frame.loc[valid_any, "label_available_ts"], utc=True)
        decision = pd.to_datetime(frame.loc[valid_any, "decision_ts"], utc=True)
        if (label_available <= decision).any():
            errors.append(f"V5.2 label_available_ts <= decision_ts for valid labels in {timeframe}")
    for h in HORIZONS:
        valid = frame[f"label_valid_h{h}"]
        expected_tail_valid = [True] * max(0, len(frame) - h) + [False] * min(h, len(frame))
        if list(valid.astype(bool)) != expected_tail_valid:
            errors.append(f"V5.2 label_valid_h{h} tail mismatch for {timeframe}")
        if (valid & frame[f"future_close_h{h}"].isna()).any():
            errors.append(f"V5.2 label_valid_h{h} true with null future_close in {timeframe}")
        if (valid & frame[f"label_end_ts_h{h}"].isna()).any():
            errors.append(f"V5.2 label_valid_h{h} true with null label_end_ts in {timeframe}")
    expected_tail = ~(frame["label_valid_h1"] & frame["label_valid_h3"] & frame["label_valid_h5"])
    if not (frame["tail_row"].astype(bool).reset_index(drop=True) == expected_tail.reset_index(drop=True)).all():
        errors.append(f"V5.2 tail_row mismatch for {timeframe}")
    return errors


def _forbidden_columns(frame: pd.DataFrame) -> list[str]:
    forbidden: list[str] = []
    for column in frame.columns:
        if column in LABEL_COLUMNS_V5_2:
            continue
        lower = str(column).casefold()
        if any(term in lower for term in FORBIDDEN_COLUMNS_V5_2):
            forbidden.append(str(column))
    return sorted(forbidden)


def _validate_manifest_quality(manifest: dict[str, Any], physical_quality: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for timeframe in TIMEFRAMES_V5_2:
        declared = manifest.get("quality", {}).get(timeframe)
        physical = physical_quality.get(timeframe)
        if not isinstance(declared, dict):
            errors.append(f"V5.2 manifest quality missing for {timeframe}")
            continue
        if not isinstance(physical, dict):
            errors.append(f"V5.2 physical quality unavailable for {timeframe}")
            continue
        for field in sorted(QUALITY_KEYS - {"warnings", "errors"}):
            if declared.get(field) != physical.get(field):
                errors.append(f"V5.2 manifest quality mismatch for {timeframe}.{field}")
        if declared.get("errors") != physical.get("errors"):
            errors.append(f"V5.2 manifest quality errors mismatch for {timeframe}")
        if declared.get("warnings") != physical.get("warnings"):
            errors.append(f"V5.2 manifest quality warnings mismatch for {timeframe}")
    return errors


def _validate_report(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_exact_keys(report, REPORT_KEYS, "V5.2 label report"))
    for field in REPORT_KEYS:
        if report.get(field) != manifest.get(field):
            errors.append(f"V5.2 label report {field} mismatch")
    errors.extend(_validate_safety(report.get("safety", {})))
    return errors


def _validate_markdown(root: Path) -> list[str]:
    path = root / REPORT_MD_PATH_V5_2
    if not path.exists():
        return [f"missing V5.2 label markdown: {REPORT_MD_PATH_V5_2}"]
    text = path.read_text(encoding="utf-8")
    errors = validate_markdown_forbidden_claims(text, "V5.2 label markdown")
    normalized = text.replace("’", "'")
    required = [
        "V5.2 ne valide aucune stratégie",
        "V5.2 ne produit aucun dataset ML",
        "V5.2 ne produit aucun modèle ML",
        "V5.2 ne produit aucun backtest",
        "V5.2 ne produit aucun signal de trading",
        "V5.2 ne produit aucun ordre",
        "V5.2 n’autorise aucun paper live",
        "V5.2 n’autorise aucun trading réel",
    ]
    for clause in required:
        if clause.replace("’", "'") not in normalized:
            errors.append(f"V5.2 label markdown missing safety clause: {clause}")
    return errors


def _validate_v5_1_features_unchanged(root: Path) -> list[str]:
    path = root / FEATURE_MANIFEST_PATH_V5_1
    if not path.exists():
        return [f"missing V5.1 feature manifest: {FEATURE_MANIFEST_PATH_V5_1}"]
    manifest = load_json(path)
    errors: list[str] = []
    for timeframe, payload in manifest.get("outputs", {}).items():
        feature_path = root / payload.get("path", "")
        if not feature_path.exists():
            errors.append(f"missing V5.1 feature output: {payload.get('path')}")
            continue
        if sha256_file(feature_path) != payload.get("sha256"):
            errors.append(f"V5.1 feature output modified during V5.2: {timeframe}")
    return errors


def _find_forbidden_v5_2_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    for prefix in FORBIDDEN_V5_2_PATHS:
        path = root / prefix
        if path.exists():
            if path.is_file():
                errors.append(f"Forbidden V5.2 artifact detected: {path.relative_to(root)}")
            else:
                children = sorted(child for child in path.rglob("*") if child.is_file())
                if children:
                    errors.extend(f"Forbidden V5.2 artifact detected: {child.relative_to(root)}" for child in children[:20])
                else:
                    errors.append(f"Forbidden V5.2 artifact detected: {path.relative_to(root)}")
    for child in sorted(root.rglob("*")):
        if any(part in IGNORED_SCAN_PARTS for part in child.relative_to(root).parts):
            continue
        if child.is_file() and child.suffix.casefold() in FORBIDDEN_MODEL_SUFFIXES:
            errors.append(f"Forbidden V5.2 model artifact detected: {child.relative_to(root)}")
    return errors


def _result(errors: list[str], **extra: Any) -> dict[str, Any]:
    return {"version": VERSION_V5_2, "passed": not errors, "errors": errors, **extra}
