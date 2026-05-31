from __future__ import annotations

from galapagos.datasets.redesigned_label_5y_dataset_v9_65 import distribution_stats_v9_65, split_series_v9_65


def test_v9_65_split_series_is_temporal_60_20_20() -> None:
    split = split_series_v9_65(10).tolist()
    assert split == ["train"] * 6 + ["validation"] * 2 + ["test"] * 2


def test_v9_65_distribution_is_binary_safe() -> None:
    stats = distribution_stats_v9_65({"-1": 50, "1": 50})
    assert stats["majority_class_ratio"] == 0.5
    assert stats["flat_ratio"] == 0.0
