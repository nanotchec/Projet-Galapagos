from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd


def generate_random_entries_same_count(
    data: pd.DataFrame,
    n: int,
    side: str = "LONG",
    seed: int | None = None,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    count = min(int(n), len(data))
    indexes = sorted(rng.choice(len(data), size=count, replace=False).tolist()) if count else []
    return _entries_from_indexes(data, indexes, side)


def generate_random_entries_same_frequency(
    data: pd.DataFrame,
    original_signal_timestamps: Iterable[Any],
    seed: int | None = None,
) -> pd.DataFrame:
    timestamps = list(original_signal_timestamps)
    return generate_random_entries_same_count(data, len(timestamps), seed=seed)


def random_forward_returns(
    labels: pd.DataFrame,
    n: int,
    horizon_column: str = "forward_return_6bar",
    seed: int | None = None,
) -> list[float]:
    entries = generate_random_entries_same_count(
        labels.dropna(subset=[horizon_column]),
        n,
        seed=seed,
    )
    if entries.empty:
        return []
    return [float(labels.loc[index, horizon_column]) for index in entries["index"]]


def _entries_from_indexes(data: pd.DataFrame, indexes: list[int], side: str) -> pd.DataFrame:
    timestamps = (
        data["timestamp"].iloc[indexes].tolist()
        if "timestamp" in data.columns
        else indexes
    )
    return pd.DataFrame(
        [
            {"index": index, "timestamp": timestamp, "side": side, "source": "random"}
            for index, timestamp in zip(indexes, timestamps, strict=True)
        ]
    )
