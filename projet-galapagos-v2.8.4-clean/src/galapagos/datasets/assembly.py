from __future__ import annotations

import pandas as pd

from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V2_7,
    DATASET_SCHEMA_VERSION,
    FEATURE_VALUE_COLUMNS,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
)
from galapagos.datasets.splits import assign_temporal_splits


def build_offline_supervised_dataset(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    feature_sha256: str,
    label_sha256: str,
    dataset_run_id: str,
) -> pd.DataFrame:
    """Builds the V2.7 offline supervised dataset without ML fitting or signal generation."""
    _require_columns(features, [*JOIN_KEYS, "feature_available_ts", *FEATURE_VALUE_COLUMNS], "features")
    _require_columns(labels, [*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS], "labels")

    feature_block = features[[*JOIN_KEYS, "feature_available_ts", *FEATURE_VALUE_COLUMNS]].copy()
    label_block = labels[[*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS]].copy()
    merged = feature_block.merge(label_block, on=JOIN_KEYS, how="inner", validate="one_to_one")

    merged["dataset_run_id"] = dataset_run_id
    merged["dataset_schema_version"] = DATASET_SCHEMA_VERSION
    merged["source_features_sha256"] = feature_sha256
    merged["source_labels_sha256"] = label_sha256

    merged = assign_temporal_splits(merged)
    merged["dataset_error_count"] = 0
    null_columns = [column for column in DATASET_COLUMNS_V2_7 if column not in {"dataset_null_count"}]
    merged["dataset_null_count"] = merged[null_columns].isna().sum(axis=1).astype(int)
    return merged[DATASET_COLUMNS_V2_7].copy()


def _require_columns(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")
