from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.multi_day_datacard import build_datacard_markdown_v3_2, build_quality_markdown_v3_2
from galapagos.datasets.multi_day_quality import assess_multi_day_dataset_quality
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V3_2,
    DATASET_SCHEMA_VERSION_V3_2,
    DOC_PATH_V3_2,
    EXPECTED_LIMITATIONS_V3_2,
    EXPECTED_ROWS_V3_2,
    FEATURE_VALUE_COLUMNS,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    MANIFEST_PATH_V3_2,
    REPORT_JSON_PATH_V3_2,
    REPORT_MD_PATH_V3_2,
    DATACARD_MD_PATH_V3_2,
    SPLIT_COLUMNS_V3_2,
    SPLIT_POLICY_V3_2,
    TIMEFRAMES_V3_2,
    VERSION_V3_2,
    get_dataset_v3_2_path,
    get_split_v3_2_path,
)

WINDOW_LABEL = "2024-01-15_2024-01-21"


def run_multi_day_offline_supervised_dataset_v3_2(
    root: Path = Path("."),
    *,
    validate_recent_layers: bool = True,
    validate_full_history: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_recent_layers:
        _validate_recent_layers(root)
    if validate_full_history:
        _validate_full_history(root)

    created_at = utc_now_iso()
    dataset_run_id = f"v3_2_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_features: dict[str, dict[str, Any]] = {}
    input_labels: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    splits: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V3_2:
        feature_path = input_feature_path(root, timeframe)
        label_path = input_label_path(root, timeframe)
        feature_frame = read_parquet(feature_path)
        label_frame = read_parquet(label_path)
        feature_sha = sha256_file(feature_path)
        label_sha = sha256_file(label_path)

        dataset = build_multi_day_offline_supervised_dataset_v3_2(
            feature_frame,
            label_frame,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
            dataset_run_id=dataset_run_id,
        )
        split_frame = build_split_frame_v3_2(dataset)

        dataset_path = get_dataset_v3_2_path(root, timeframe)
        split_path = get_split_v3_2_path(root, timeframe)
        write_parquet(dataset, dataset_path)
        write_parquet(split_frame, split_path)

        input_features[timeframe] = _input_block(root, feature_path, feature_sha, len(feature_frame))
        input_labels[timeframe] = _input_block(root, label_path, label_sha, len(label_frame))
        outputs[timeframe] = _output_block(root, dataset_path, len(dataset))
        splits[timeframe] = _output_block(root, split_path, len(split_frame))
        quality[timeframe] = assess_multi_day_dataset_quality(
            dataset,
            expected_rows=EXPECTED_ROWS_V3_2[timeframe],
            timeframe=timeframe,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
        )
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION_V3_2,
        "status": status,
        "created_at_utc": created_at,
        "dataset_run_id": dataset_run_id,
        "input_features": input_features,
        "input_labels": input_labels,
        "outputs": outputs,
        "splits": splits,
        "dataset_schema_version": DATASET_SCHEMA_VERSION_V3_2,
        "dataset_columns": DATASET_COLUMNS_V3_2,
        "split_policy": SPLIT_POLICY_V3_2,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V3_2,
    }
    _write_json(root / MANIFEST_PATH_V3_2, manifest)
    _write_json(root / REPORT_JSON_PATH_V3_2, manifest)
    quality_markdown = build_quality_markdown_v3_2(manifest)
    datacard = build_datacard_markdown_v3_2(manifest)
    _write_text(root / REPORT_MD_PATH_V3_2, quality_markdown)
    _write_text(root / DATACARD_MD_PATH_V3_2, datacard)
    _write_text(root / DOC_PATH_V3_2, quality_markdown)
    return manifest


def build_multi_day_offline_supervised_dataset_v3_2(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    feature_sha256: str,
    label_sha256: str,
    dataset_run_id: str,
) -> pd.DataFrame:
    _require_columns(features, [*JOIN_KEYS, "feature_available_ts", *FEATURE_VALUE_COLUMNS], "features")
    _require_columns(labels, [*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS], "labels")

    feature_block = features[[*JOIN_KEYS, "feature_available_ts", *FEATURE_VALUE_COLUMNS]].copy()
    label_block = labels[[*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS]].copy()
    merged = feature_block.merge(label_block, on=JOIN_KEYS, how="inner", validate="one_to_one")
    merged = merged.sort_values("event_ts").reset_index(drop=True)
    merged["dataset_run_id"] = dataset_run_id
    merged["dataset_schema_version"] = DATASET_SCHEMA_VERSION_V3_2
    merged["source_features_sha256"] = feature_sha256
    merged["source_labels_sha256"] = label_sha256
    merged = assign_temporal_splits_v3_2(merged)
    merged["dataset_error_count"] = 0
    null_columns = [column for column in DATASET_COLUMNS_V3_2 if column != "dataset_null_count"]
    merged["dataset_null_count"] = merged[null_columns].isna().sum(axis=1).astype(int)
    return merged[DATASET_COLUMNS_V3_2].copy()


def assign_temporal_splits_v3_2(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values("event_ts").reset_index(drop=True).copy()
    rows = len(ordered)
    train_end = int(rows * SPLIT_POLICY_V3_2["train_ratio"])
    validation_end = train_end + int(rows * SPLIT_POLICY_V3_2["validation_ratio"])
    ordered["split"] = "test"
    ordered.loc[: train_end - 1, "split"] = "train"
    ordered.loc[train_end : validation_end - 1, "split"] = "validation"
    ordered["split_order"] = range(rows)
    ordered["purge_embargo_group"] = SPLIT_POLICY_V3_2["purge_embargo"]
    return ordered


def build_split_frame_v3_2(dataset: pd.DataFrame) -> pd.DataFrame:
    _require_columns(dataset, SPLIT_COLUMNS_V3_2, "dataset")
    return dataset[SPLIT_COLUMNS_V3_2].copy()


def input_feature_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_0/features/ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_LABEL}"
        / "features.parquet"
    )


def input_label_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_1/labels/forward_returns"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_LABEL}"
        / "labels.parquet"
    )


def _validate_recent_layers(root: Path) -> None:
    from galapagos.data.public_market.multi_day_validation import validate_multi_day_public_market_data_v2_9
    from galapagos.features.multi_day_validation import validate_multi_day_causal_feature_store_v3_0
    from galapagos.labels.multi_day_validation import validate_multi_day_label_factory_v3_1

    validators = [
        ("V2.9.1 multi-day OHLCV", validate_multi_day_public_market_data_v2_9),
        ("V3.0 multi-day features", validate_multi_day_causal_feature_store_v3_0),
        ("V3.1 multi-day labels", validate_multi_day_label_factory_v3_1),
    ]
    for label, validator in validators:
        result = validator(root)
        if not result["passed"]:
            raise RuntimeError(f"{label} validation failed before V3.2: {result['errors']}")


def _validate_full_history(root: Path) -> None:
    from galapagos.datasets.validation import validate_offline_supervised_dataset_v2_7
    from galapagos.features.validation import validate_causal_feature_store_v2_5
    from galapagos.labels.validation import validate_label_factory_v2_6
    from galapagos.ml.validation import validate_offline_ml_research_v2_8
    from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
    from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4

    validators = [
        ("V2.3.1 ingestion", validate_public_market_ingestion_v2_3),
        ("V2.4.8 resampling", validate_ohlcv_resampling_v2_4),
        ("V2.5.2 features", validate_causal_feature_store_v2_5),
        ("V2.6.2 labels", validate_label_factory_v2_6),
        ("V2.7.2 dataset", validate_offline_supervised_dataset_v2_7),
        ("V2.8.4 offline ML", validate_offline_ml_research_v2_8),
    ]
    for label, validator in validators:
        result = validator(root)
        if not result["passed"]:
            raise RuntimeError(f"{label} validation failed before V3.2: {result['errors']}")


def _input_block(root: Path, path: Path, sha256: str, rows: int) -> dict[str, Any]:
    return {"path": str(path.relative_to(root)), "sha256": sha256, "rows": int(rows)}


def _output_block(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(root)),
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
        raise ValueError(f"{label} missing required columns: {missing}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
