from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.refined_ohlcv_trades_window_datacard import build_datacard_markdown_v9_1, build_quality_markdown_v9_1
from galapagos.datasets.refined_ohlcv_trades_window_quality import assess_refined_ohlcv_trades_dataset_quality_v9_1
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V9_1,
    DATASET_SCHEMA_VERSION_V9_1,
    DATACARD_MD_PATH_V9_1,
    DOC_PATH_V9_1,
    EXPECTED_LIMITATIONS_V9_1,
    EXPECTED_ROWS_V9_1,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    MANIFEST_PATH_V9_1,
    REFINED_OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V9_1,
    REPORT_JSON_PATH_V9_1,
    REPORT_MD_PATH_V9_1,
    SPLIT_COLUMNS_V9_1,
    SPLIT_POLICY_V9_1,
    TIMEFRAMES_V9_1,
    VERSION_V9_1,
    get_dataset_v9_1_path,
    get_split_v9_1_path,
)
from galapagos.features.refined_ohlcv_trades_validation import validate_refined_ohlcv_trades_feature_store_v9_0
from galapagos.features.refined_ohlcv_trades_schemas import (
    MANIFEST_PATH_V9_0 as FEATURE_MANIFEST_PATH_V9_0,
    WINDOW_END_V9_0,
    WINDOW_START_V9_0,
)
from galapagos.labels.max_history_window import MANIFEST_PATH_V5_2 as LABEL_MANIFEST_PATH_V5_2
from galapagos.labels.max_history_window_validation import validate_max_history_label_factory_v5_2


WINDOW_START_V9_1 = WINDOW_START_V9_0
WINDOW_END_V9_1 = WINDOW_END_V9_0
TOTAL_DAYS_V9_1 = 366


def run_refined_ohlcv_trades_offline_supervised_dataset_v9_1(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    project_root = root.resolve()
    if validate_inputs:
        _validate_inputs(project_root)

    feature_manifest = load_v9_0_feature_manifest(project_root)
    label_manifest = load_v5_2_label_manifest(project_root)
    _validate_input_windows(feature_manifest, label_manifest)

    created_at = utc_now_iso()
    dataset_run_id = f"v9_1_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_features: dict[str, dict[str, Any]] = {}
    input_labels_filtered: dict[str, dict[str, int]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    splits: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V9_1:
        feature_path = input_feature_path(project_root, timeframe, feature_manifest)
        label_path = input_label_path(project_root, timeframe, label_manifest)
        feature_frame = read_parquet(feature_path)
        label_frame = filter_labels_to_v9_1_window(read_parquet(label_path))
        feature_sha = sha256_file(feature_path)
        label_sha = sha256_file(label_path)
        expected_rows = EXPECTED_ROWS_V9_1[timeframe]
        if len(feature_frame) != expected_rows or len(label_frame) != expected_rows:
            raise RuntimeError(
                f"V9.1 input row count mismatch for {timeframe}: features={len(feature_frame)}, "
                f"filtered_labels={len(label_frame)}, expected={expected_rows}"
            )

        dataset = build_refined_ohlcv_trades_offline_supervised_dataset_v9_1(
            feature_frame,
            label_frame,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
            dataset_run_id=dataset_run_id,
        )
        split_frame = build_split_frame_v9_1(dataset)
        dataset_path = dataset_output_path(project_root, timeframe, WINDOW_START_V9_1, WINDOW_END_V9_1)
        split_path = split_output_path(project_root, timeframe, WINDOW_START_V9_1, WINDOW_END_V9_1)
        write_parquet(dataset, dataset_path)
        write_parquet(split_frame, split_path)

        input_features[timeframe] = _input_block(project_root, feature_path, feature_sha, len(feature_frame))
        input_labels_filtered[timeframe] = {"rows": int(len(label_frame))}
        outputs[timeframe] = _output_block(project_root, dataset_path, len(dataset))
        splits[timeframe] = _output_block(project_root, split_path, len(split_frame))
        quality[timeframe] = assess_refined_ohlcv_trades_dataset_quality_v9_1(
            dataset,
            split_frame,
            expected_rows=expected_rows,
            timeframe=timeframe,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
        )
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION_V9_1,
        "status": status,
        "created_at_utc": created_at,
        "dataset_run_id": dataset_run_id,
        "input_features_manifest": {
            "path": FEATURE_MANIFEST_PATH_V9_0.as_posix(),
            "sha256": sha256_file(project_root / FEATURE_MANIFEST_PATH_V9_0),
            "window_start": feature_manifest["window"]["window_start"],
            "window_end": feature_manifest["window"]["window_end"],
            "total_days": int(feature_manifest["window"]["total_days"]),
        },
        "input_labels_manifest": {
            "path": LABEL_MANIFEST_PATH_V5_2.as_posix(),
            "sha256": sha256_file(project_root / LABEL_MANIFEST_PATH_V5_2),
            "source_window_start": label_manifest["input_ohlcv_manifest"]["window_start"],
            "source_window_end": label_manifest["input_ohlcv_manifest"]["window_end"],
            "dataset_window_start": WINDOW_START_V9_1,
            "dataset_window_end": WINDOW_END_V9_1,
        },
        "input_features": input_features,
        "input_labels_filtered": input_labels_filtered,
        "outputs": outputs,
        "splits": splits,
        "dataset_schema_version": DATASET_SCHEMA_VERSION_V9_1,
        "dataset_columns": DATASET_COLUMNS_V9_1,
        "feature_columns_count": len(REFINED_OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V9_1),
        "split_policy": SPLIT_POLICY_V9_1,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V9_1,
    }
    report = build_report_v9_1(manifest)
    _write_json(project_root / MANIFEST_PATH_V9_1, manifest)
    _write_json(project_root / REPORT_JSON_PATH_V9_1, report)
    quality_markdown = build_quality_markdown_v9_1(manifest)
    datacard = build_datacard_markdown_v9_1(manifest)
    _write_text(project_root / REPORT_MD_PATH_V9_1, quality_markdown)
    _write_text(project_root / DATACARD_MD_PATH_V9_1, datacard)
    _write_text(project_root / DOC_PATH_V9_1, quality_markdown)
    return manifest


def build_refined_ohlcv_trades_offline_supervised_dataset_v9_1(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    feature_sha256: str,
    label_sha256: str,
    dataset_run_id: str,
) -> pd.DataFrame:
    _require_columns(features, [*JOIN_KEYS, "feature_available_ts", *REFINED_OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V9_1], "refined features")
    _require_columns(labels, [*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS], "labels")
    feature_block = (
        features[[*JOIN_KEYS, "feature_available_ts", *REFINED_OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V9_1]]
        .sort_values("event_ts")
        .reset_index(drop=True)
    )
    label_block = labels[[*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS]].sort_values("event_ts").reset_index(drop=True)
    if len(feature_block) != len(label_block):
        raise RuntimeError(f"V9.1 source row count mismatch: features={len(feature_block)}, labels={len(label_block)}")
    try:
        pd.testing.assert_frame_equal(feature_block[JOIN_KEYS], label_block[JOIN_KEYS], check_dtype=False)
    except AssertionError as exc:
        raise RuntimeError(f"V9.1 join key mismatch: {str(exc).splitlines()[0]}") from exc

    merged = pd.concat(
        [
            feature_block[[*JOIN_KEYS, "feature_available_ts", *REFINED_OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V9_1]],
            label_block[["label_available_ts", *LABEL_VALUE_COLUMNS]],
        ],
        axis=1,
    )
    merged["dataset_run_id"] = dataset_run_id
    merged["dataset_schema_version"] = DATASET_SCHEMA_VERSION_V9_1
    merged["source_features_sha256"] = feature_sha256
    merged["source_labels_sha256"] = label_sha256
    merged = assign_temporal_splits_v9_1(merged)
    merged["dataset_error_count"] = 0
    null_columns = [column for column in DATASET_COLUMNS_V9_1 if column != "dataset_null_count"]
    merged["dataset_null_count"] = merged[null_columns].isna().sum(axis=1).astype("int16")
    return merged[DATASET_COLUMNS_V9_1].copy()


def assign_temporal_splits_v9_1(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values("event_ts").reset_index(drop=True).copy()
    rows = len(ordered)
    train_end = int(rows * SPLIT_POLICY_V9_1["train_ratio"])
    validation_rows = (rows - train_end) // 2
    validation_end = train_end + validation_rows
    ordered["split"] = "test"
    ordered.loc[: train_end - 1, "split"] = "train"
    ordered.loc[train_end : validation_end - 1, "split"] = "validation"
    ordered["split_order"] = range(rows)
    ordered["purge_embargo_group"] = SPLIT_POLICY_V9_1["purge_embargo"]
    event_ts = pd.to_datetime(ordered["event_ts"], utc=True)
    month_labels = event_ts.dt.strftime("wf_%Y_%m")
    ordered["walk_forward_group"] = month_labels.mask(month_labels == "wf_2023_03", "wf_2023_03_partial").mask(
        month_labels == "wf_2024_03",
        "wf_2024_03_partial",
    )
    return ordered


def build_split_frame_v9_1(dataset: pd.DataFrame) -> pd.DataFrame:
    _require_columns(dataset, SPLIT_COLUMNS_V9_1, "dataset")
    return dataset[SPLIT_COLUMNS_V9_1].copy()


def filter_labels_to_v9_1_window(labels: pd.DataFrame) -> pd.DataFrame:
    event_ts = pd.to_datetime(labels["event_ts"], utc=True)
    start = pd.Timestamp(f"{WINDOW_START_V9_1}T00:00:00Z")
    end_exclusive = pd.Timestamp("2024-03-25T00:00:00Z")
    return labels.loc[(event_ts >= start) & (event_ts < end_exclusive)].sort_values("event_ts").reset_index(drop=True)


def load_v9_0_feature_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / FEATURE_MANIFEST_PATH_V9_0).read_text(encoding="utf-8"))


def load_v5_2_label_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / LABEL_MANIFEST_PATH_V5_2).read_text(encoding="utf-8"))


def input_feature_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v9_0_feature_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def input_label_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v5_2_label_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def dataset_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    return get_dataset_v9_1_path(root.resolve(), timeframe, window_start or WINDOW_START_V9_1, window_end or WINDOW_END_V9_1)


def split_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    return get_split_v9_1_path(root.resolve(), timeframe, window_start or WINDOW_START_V9_1, window_end or WINDOW_END_V9_1)


def build_report_v9_1(manifest: dict[str, Any]) -> dict[str, Any]:
    return dict(manifest)


def _validate_inputs(root: Path) -> None:
    feature_validation = validate_refined_ohlcv_trades_feature_store_v9_0(root)
    if not feature_validation["passed"]:
        raise RuntimeError(f"V9.0 validation failed before V9.1: {feature_validation['errors']}")
    label_validation = validate_max_history_label_factory_v5_2(root)
    if not label_validation["passed"]:
        raise RuntimeError(f"V5.2 validation failed before V9.1: {label_validation['errors']}")


def _validate_input_windows(feature_manifest: dict[str, Any], label_manifest: dict[str, Any]) -> None:
    if feature_manifest["window"]["window_start"] != WINDOW_START_V9_1 or feature_manifest["window"]["window_end"] != WINDOW_END_V9_1:
        raise ValueError("V9.1 requires the exact V9.0 feature window.")
    if int(feature_manifest["window"]["total_days"]) != TOTAL_DAYS_V9_1:
        raise ValueError("V9.1 requires a 1-year V9.0 feature window.")
    label_window_start = label_manifest["input_ohlcv_manifest"]["window_start"]
    label_window_end = label_manifest["input_ohlcv_manifest"]["window_end"]
    if WINDOW_START_V9_1 < label_window_start or WINDOW_END_V9_1 > label_window_end:
        raise ValueError("V9.1 labels V5.2 must cover the full V9.0 window.")


def _input_block(root: Path, path: Path, sha256: str, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "sha256": sha256, "rows": int(rows)}


def _output_block(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(rows),
        "format": "parquet",
    }


def _safety() -> dict[str, bool]:
    return {
        "public_read_only": True,
        "authentication_used": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "orders_enabled": False,
        "paper_live_enabled": False,
        "trading_enabled": False,
        "ml_enabled": False,
        "labels_enabled": True,
        "dataset_enabled": True,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "execution_enabled": False,
    }


def _require_columns(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise RuntimeError(f"Missing {label} columns: {missing}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
