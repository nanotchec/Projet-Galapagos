from __future__ import annotations

import pandas as pd
import numpy as np

from galapagos.labels.refined_volatility_normalized_labels_v9_6 import (
    build_refined_volatility_normalized_labels_frame_v9_6,
    leakage_guard_v9_6,
    select_volatility_multiplier_v9_6,
)
from galapagos.labels.refined_volatility_normalized_labels_v9_6_schemas import (
    PARAMETER_GRID_V9_6,
    REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6,
    TARGET_NAME_V9_6,
)


def _sample_dataset(rows: int = 48) -> pd.DataFrame:
    event_ts = pd.date_range("2023-03-25", periods=rows, freq="min", tz="UTC")
    close = pd.Series([100 + index * 0.1 for index in range(rows)], dtype=float)
    future = close.shift(-1).combine(close, lambda nxt, cur: 0.0 if pd.isna(nxt) else float(np.log(nxt / cur)))
    return pd.DataFrame(
        {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "event_ts": event_ts,
            "close_ts": event_ts + pd.Timedelta(seconds=59),
            "decision_ts": event_ts + pd.Timedelta(seconds=59),
            "close": close,
            "future_log_return_h1": future,
            "label_end_ts_h1": event_ts + pd.Timedelta(minutes=1, seconds=59),
            "warmup_row": False,
        }
    )


def test_build_volnorm_labels_schema_and_target_v9_6() -> None:
    labels = build_refined_volatility_normalized_labels_frame_v9_6(
        _sample_dataset(),
        source_dataset_path="sample.parquet",
        source_dataset_version="V9.1",
        label_run_id="test",
        volatility_threshold_multiplier=0.5,
    )
    assert list(labels.columns) == REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6
    assert set(labels["target_name"]) == {TARGET_NAME_V9_6}


def test_build_volnorm_labels_temporal_availability_v9_6() -> None:
    labels = build_refined_volatility_normalized_labels_frame_v9_6(
        _sample_dataset(),
        source_dataset_path="sample.parquet",
        source_dataset_version="V9.1",
        label_run_id="test",
        volatility_threshold_multiplier=0.5,
    )
    assert (pd.to_datetime(labels["label_available_ts"], utc=True) > pd.to_datetime(labels["decision_ts"], utc=True)).all()


def test_volnorm_leakage_guard_passes_v9_6() -> None:
    guard = leakage_guard_v9_6()
    assert guard["passed"] is True
    assert guard["future_return_used_only_for_label"] is True


def test_select_multiplier_uses_parameter_grid_v9_6() -> None:
    audit = {
        timeframe: {
            f"k_{k:.2f}": {
                "majority_rate": 0.45 + k / 10,
                "entropy_bits": 1.4 - k / 20,
                "class_distribution": {"FLAT": {"rate": 0.45 + k / 10}},
            }
            for k in PARAMETER_GRID_V9_6
        }
        for timeframe in ["1m", "5m", "15m", "1h"]
    }
    assert select_volatility_multiplier_v9_6(audit) in PARAMETER_GRID_V9_6
