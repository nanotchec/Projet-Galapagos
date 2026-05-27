from __future__ import annotations

import pandas as pd

from galapagos.datasets.refined_volnorm_labels_dataset_v9_7 import assign_temporal_splits_v9_7, build_split_frame_v9_7
from galapagos.datasets.refined_volnorm_labels_dataset_v9_7_schemas import SPLIT_COLUMNS_V9_7, SPLIT_POLICY_V9_7


def test_v9_7_split_policy_is_temporal_no_shuffle() -> None:
    assert SPLIT_POLICY_V9_7["shuffle"] is False
    assert SPLIT_POLICY_V9_7["train_ratio"] == 0.60
    assert SPLIT_POLICY_V9_7["walk_forward_group"] == "calendar_month"


def test_assign_temporal_splits_v9_7_orders_roles() -> None:
    frame = pd.DataFrame({"event_ts": pd.date_range("2023-03-25", periods=10, freq="h", tz="UTC")})
    split = assign_temporal_splits_v9_7(frame)
    assert split["split"].tolist() == ["train"] * 6 + ["validation"] * 2 + ["test"] * 2
    assert split["split_order"].is_monotonic_increasing


def test_build_split_frame_v9_7_schema() -> None:
    frame = pd.DataFrame({column: [] for column in SPLIT_COLUMNS_V9_7})
    assert list(build_split_frame_v9_7(frame).columns) == SPLIT_COLUMNS_V9_7
