from __future__ import annotations

import pandas as pd

from galapagos.datasets.schemas import JOIN_KEYS, SPLIT_COLUMNS_V2_7


def assign_temporal_splits(frame: pd.DataFrame) -> pd.DataFrame:
    """Assigns deterministic 60/20/20 train/validation/test splits without shuffling."""
    ordered = frame.sort_values("event_ts", kind="mergesort").reset_index(drop=True).copy()
    rows = len(ordered)
    train_end = int(rows * 0.6)
    validation_end = train_end + int(rows * 0.2)

    split = ["train"] * train_end
    split.extend(["validation"] * (validation_end - train_end))
    split.extend(["test"] * (rows - validation_end))

    ordered["split"] = split
    ordered["split_order"] = range(rows)
    ordered["purge_embargo_group"] = "none_v2_7_preview"
    return ordered


def build_split_frame(dataset: pd.DataFrame) -> pd.DataFrame:
    return dataset[SPLIT_COLUMNS_V2_7].copy()


def split_temporal_order_valid(frame: pd.DataFrame) -> bool:
    if "split" not in frame.columns or "split_order" not in frame.columns or "event_ts" not in frame.columns:
        return False
    ordered = frame.sort_values("split_order", kind="mergesort")
    if not pd.to_datetime(ordered["event_ts"], utc=True).is_monotonic_increasing:
        return False
    split_rank = ordered["split"].map({"train": 0, "validation": 1, "test": 2})
    if split_rank.isna().any():
        return False
    return bool(split_rank.is_monotonic_increasing)
