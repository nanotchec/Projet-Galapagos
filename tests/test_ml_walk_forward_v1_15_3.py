from datetime import UTC

import pandas as pd

from galapagos.research.ml.walk_forward import build_date_based_walk_forward_splits


def test_date_based_walk_forward_non_range_index() -> None:
    # Create dataset with non-range index
    dates = pd.date_range("2022-01-01", periods=100, freq="D", tz=UTC)
    df = pd.DataFrame({"timestamp": dates, "val": range(100)})
    df.index = [f"idx_{i}" for i in range(100)]  # Non-RangeIndex, string index

    config = {
        "walk_forward": {
            "embargo_bars": 2,
            "date_windows": [
                {
                    "name": "test_window",
                    "train_start": "2022-01-01",
                    "train_end": "2022-01-10",
                    "test_start": "2022-01-15",
                    "test_end": "2022-01-20",
                }
            ]
        }
    }

    windows = build_date_based_walk_forward_splits(df, config)
    assert len(windows) == 1
    w = windows[0]
    
    assert w.name == "test_window"
    # Train ends at index 9 (inclusive, so train_end=10)
    assert w.train_start == 0
    assert w.train_end == 10
    
    # Test starts at 2022-01-15 which is index 14
    assert w.test_start == 14
    # Test ends at 2022-01-20 which is index 19 (inclusive, so test_end=20)
    assert w.test_end == 20
