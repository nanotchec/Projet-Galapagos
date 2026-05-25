from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from galapagos.datasets.ohlcv_trades_1y_window import (
    dataset_output_path,
    filter_labels_to_v8_4_window,
    input_feature_path,
    input_label_path,
    load_v5_2_label_manifest,
    load_v8_3_feature_manifest,
    split_output_path,
)
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V8_4,
    EXPECTED_ROWS_V8_4,
    EXPECTED_SPLIT_COUNTS_V8_4,
    FORBIDDEN_DATASET_COLUMNS_EXACT_V8_4,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4,
    SPLIT_COLUMNS_V8_4,
    TIMEFRAMES_V8_4,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def manifests() -> tuple[dict, dict]:
    return load_v8_3_feature_manifest(ROOT), load_v5_2_label_manifest(ROOT)


def test_ohlcv_trades_1y_dataset_row_count_matches_features_and_filtered_labels(manifests: tuple[dict, dict]) -> None:
    feature_manifest, label_manifest = manifests
    for timeframe in TIMEFRAMES_V8_4:
        dataset_path = dataset_output_path(ROOT, timeframe)
        assert _parquet_rows(dataset_path) == _parquet_rows(input_feature_path(ROOT, timeframe, feature_manifest))
        assert _parquet_rows(dataset_path) == len(_filtered_labels(input_label_path(ROOT, timeframe, label_manifest)))
        assert _parquet_rows(dataset_path) == EXPECTED_ROWS_V8_4[timeframe]


def test_ohlcv_trades_1y_dataset_strict_columns() -> None:
    for timeframe in TIMEFRAMES_V8_4:
        assert _parquet_columns(dataset_output_path(ROOT, timeframe)) == DATASET_COLUMNS_V8_4
        assert _parquet_columns(split_output_path(ROOT, timeframe)) == SPLIT_COLUMNS_V8_4


def test_ohlcv_trades_1y_dataset_join_keys_match_sources(manifests: tuple[dict, dict]) -> None:
    feature_manifest, label_manifest = manifests
    features = _read_columns(input_feature_path(ROOT, "15m", feature_manifest), JOIN_KEYS)
    labels = filter_labels_to_v8_4_window(_read_columns(input_label_path(ROOT, "15m", label_manifest), JOIN_KEYS))
    dataset = _read_columns(dataset_output_path(ROOT, "15m"), JOIN_KEYS)
    pd.testing.assert_frame_equal(dataset, features, check_dtype=False)
    pd.testing.assert_frame_equal(dataset, labels[JOIN_KEYS], check_dtype=False)


def test_ohlcv_trades_1y_dataset_feature_values_match_source(manifests: tuple[dict, dict]) -> None:
    feature_manifest, _label_manifest = manifests
    columns = [
        "agg_trade_count",
        "agg_trade_vwap",
        "taker_buy_ratio_quantity",
        "trade_flow_pressure",
        "warmup_row",
        "trades_feature_null_count",
    ]
    features = _read_columns(input_feature_path(ROOT, "1h", feature_manifest), columns)
    dataset = _read_columns(dataset_output_path(ROOT, "1h"), columns)
    pd.testing.assert_frame_equal(dataset, features, check_dtype=False, check_exact=False, atol=1e-9, rtol=1e-9)


def test_ohlcv_trades_1y_dataset_label_values_match_source(manifests: tuple[dict, dict]) -> None:
    _feature_manifest, label_manifest = manifests
    columns = ["future_close_h1", "future_log_return_h3", "up_down_flat_h5", "tail_row"]
    labels = filter_labels_to_v8_4_window(_read_columns(input_label_path(ROOT, "1h", label_manifest), [*columns, "event_ts"]))
    dataset = _read_columns(dataset_output_path(ROOT, "1h"), columns)
    pd.testing.assert_frame_equal(dataset, labels[columns], check_dtype=False, check_exact=False, atol=1e-12, rtol=1e-12)


def test_ohlcv_trades_1y_dataset_contains_trade_feature_columns() -> None:
    columns = _parquet_columns(dataset_output_path(ROOT, "1h"))
    expected_trade_columns = [
        "agg_trade_count",
        "agg_trade_quantity_sum",
        "agg_trade_quote_quantity_sum",
        "taker_buy_quantity",
        "taker_imbalance_quantity",
        "trade_flow_pressure",
    ]
    for feature_column in expected_trade_columns:
        assert feature_column in columns
        assert feature_column in OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4


def test_ohlcv_trades_1y_split_counts_sum_to_rows() -> None:
    for timeframe in TIMEFRAMES_V8_4:
        splits = _read_columns(split_output_path(ROOT, timeframe), ["split"])
        counts = {key: int(value) for key, value in splits["split"].value_counts().to_dict().items()}
        assert sum(counts.values()) == EXPECTED_ROWS_V8_4[timeframe]
        assert counts == EXPECTED_SPLIT_COUNTS_V8_4[timeframe]


def test_ohlcv_trades_1y_split_temporal_order() -> None:
    splits = _read_columns(split_output_path(ROOT, "15m"), ["event_ts", "split", "split_order"])
    assert splits["split_order"].is_monotonic_increasing
    assert pd.to_datetime(splits["event_ts"], utc=True).is_monotonic_increasing
    assert splits["split"].map({"train": 0, "validation": 1, "test": 2}).is_monotonic_increasing


def test_ohlcv_trades_1y_walk_forward_groups_present() -> None:
    splits = _read_columns(split_output_path(ROOT, "1h"), ["walk_forward_group"])
    assert splits["walk_forward_group"].notna().all()
    assert set(splits["walk_forward_group"].unique()) == {
        "wf_2023_03_partial",
        "wf_2023_04",
        "wf_2023_05",
        "wf_2023_06",
        "wf_2023_07",
        "wf_2023_08",
        "wf_2023_09",
        "wf_2023_10",
        "wf_2023_11",
        "wf_2023_12",
        "wf_2024_01",
        "wf_2024_02",
        "wf_2024_03_partial",
    }


def test_ohlcv_trades_1y_feature_available_ts_not_after_decision_ts() -> None:
    for timeframe in TIMEFRAMES_V8_4:
        dataset = _read_columns(dataset_output_path(ROOT, timeframe), ["feature_available_ts", "decision_ts"])
        assert (pd.to_datetime(dataset["feature_available_ts"], utc=True) <= pd.to_datetime(dataset["decision_ts"], utc=True)).all()


def test_ohlcv_trades_1y_label_available_ts_after_decision_ts_for_valid_labels() -> None:
    dataset = _read_columns(
        dataset_output_path(ROOT, "1h"),
        ["label_available_ts", "decision_ts", "label_valid_h1", "label_valid_h3", "label_valid_h5"],
    )
    valid = dataset[["label_valid_h1", "label_valid_h3", "label_valid_h5"]].any(axis=1)
    assert (
        pd.to_datetime(dataset.loc[valid, "label_available_ts"], utc=True)
        > pd.to_datetime(dataset.loc[valid, "decision_ts"], utc=True)
    ).all()


def test_ohlcv_trades_1y_no_forbidden_dataset_columns() -> None:
    forbidden_exact = set(FORBIDDEN_DATASET_COLUMNS_EXACT_V8_4)
    for timeframe in TIMEFRAMES_V8_4:
        columns = _parquet_columns(dataset_output_path(ROOT, timeframe))
        present = sorted(column for column in columns if column.casefold() in forbidden_exact)
        assert present == []
        assert set(LABEL_VALUE_COLUMNS).issubset(columns)


def _filtered_labels(path: Path) -> pd.DataFrame:
    return filter_labels_to_v8_4_window(pd.read_parquet(path, engine="pyarrow"))


def _parquet_rows(path: Path) -> int:
    return pq.ParquetFile(path).metadata.num_rows


def _parquet_columns(path: Path) -> list[str]:
    return pq.ParquetFile(path).schema.names


def _read_columns(path: Path, columns: list[str]) -> pd.DataFrame:
    return pd.read_parquet(path, columns=columns, engine="pyarrow")
