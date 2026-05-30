from __future__ import annotations

import pandas as pd

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_41 import (
    assemble_dataset_frame_v9_41,
    split_series_v9_41,
)
from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_41_schemas import FEATURE_COLUMNS, SELECTED_PRIMARY_LABEL


def test_split_series_is_temporal_and_non_shuffled() -> None:
    split = split_series_v9_41(10).tolist()

    assert split == ["train", "train", "train", "train", "train", "train", "validation", "validation", "test", "test"]


def test_assemble_dataset_uses_selected_h1_target_not_h4_label_valid() -> None:
    features = _feature_frame(6)
    labels = _label_frame(6)
    labels.loc[4, "label_valid"] = False
    labels.loc[4, SELECTED_PRIMARY_LABEL] = 1
    labels.loc[5, SELECTED_PRIMARY_LABEL] = pd.NA

    dataset = assemble_dataset_frame_v9_41(features, labels, "1h", "test_run")

    assert dataset.loc[4, "row_valid_for_dataset"].item() is True
    assert dataset.loc[4, "label_valid"].item() is False
    assert dataset.loc[5, "row_valid_for_dataset"].item() is False
    assert dataset.loc[5, "dataset_invalid_reason"] == "target_unavailable"
    assert dataset["target_name"].unique().tolist() == [SELECTED_PRIMARY_LABEL]


def test_assemble_dataset_blocks_label_available_before_decision() -> None:
    features = _feature_frame(4)
    labels = _label_frame(4)
    features.loc[3, "close_ts"] = features.loc[2, "decision_ts"] - pd.Timedelta(milliseconds=1)

    dataset = assemble_dataset_frame_v9_41(features, labels, "1h", "test_run")

    assert dataset.loc[2, "row_valid_for_dataset"].item() is False
    assert dataset.loc[2, "dataset_invalid_reason"] == "label_available_not_after_decision"


def _feature_frame(rows: int) -> pd.DataFrame:
    ts = pd.date_range("2021-05-05", periods=rows, freq="h", tz="UTC")
    data = {
        "source": ["binance_archive"] * rows,
        "venue": ["binance"] * rows,
        "market_type": ["spot"] * rows,
        "symbol": ["BTCUSDT"] * rows,
        "timeframe": ["1h"] * rows,
        "event_ts": ts,
        "open_ts": ts,
        "close_ts": ts + pd.Timedelta(hours=1),
        "decision_ts": ts + pd.Timedelta(hours=1),
        "available_ts": ts + pd.Timedelta(hours=1),
        "feature_available_ts": ts + pd.Timedelta(hours=1),
        "feature_schema_version": ["test_features"] * rows,
        "warmup_row": [False] * rows,
        "zero_trade_bucket": [False] * rows,
        "feature_null_count": [0] * rows,
        "feature_error_count": [0] * rows,
        "row_valid_for_features": [True] * rows,
        "feature_invalid_reason": [""] * rows,
    }
    for index, column in enumerate(FEATURE_COLUMNS):
        data[column] = [float(index + 1)] * rows
    return pd.DataFrame(data)


def _label_frame(rows: int) -> pd.DataFrame:
    ts = pd.date_range("2021-05-05", periods=rows, freq="h", tz="UTC")
    return pd.DataFrame(
        {
            "source": ["binance_archive"] * rows,
            "venue": ["binance"] * rows,
            "market_type": ["spot"] * rows,
            "symbol": ["BTCUSDT"] * rows,
            "timeframe": ["1h"] * rows,
            "event_ts": ts,
            "decision_ts": ts + pd.Timedelta(hours=1),
            "label_available_ts": ts + pd.Timedelta(hours=2),
            "label_schema_version": ["test_labels"] * rows,
            "up_down_flat_volnorm_h1_5y": pd.Series([0, 1, -1, 0, 1, -1][:rows], dtype="Int8"),
            "up_down_flat_volnorm_h4_5y": pd.Series([0, 0, 1, -1, pd.NA, pd.NA][:rows], dtype="Int8"),
            "binary_directional_volnorm_h4_5y": pd.Series([1, 1, -1, -1, pd.NA, pd.NA][:rows], dtype="Int8"),
            "label_valid": [True] * rows,
            "label_invalid_reason": [""] * rows,
            "label_null_count": [0] * rows,
            "label_error_count": [0] * rows,
        }
    )
