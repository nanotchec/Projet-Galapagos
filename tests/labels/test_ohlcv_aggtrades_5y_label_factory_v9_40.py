from __future__ import annotations

import numpy as np
import pandas as pd

from galapagos.labels.ohlcv_aggtrades_5y_label_factory_v9_40 import (
    create_label_frame_v9_40,
    future_log_return_v9_40,
)
from galapagos.labels.ohlcv_aggtrades_5y_label_factory_v9_40_schemas import REQUIRED_LABEL_COLUMNS


def test_future_log_return_uses_only_future_bars() -> None:
    returns = np.array([0.0, 0.01, 0.02, -0.03, 0.04])

    result = future_log_return_v9_40(returns, horizon_bars=2)

    assert np.allclose(result[:3], [0.03, -0.01, 0.01])
    assert np.isnan(result[3])
    assert np.isnan(result[4])


def test_create_label_frame_produces_required_schema_and_causal_available_ts() -> None:
    timestamps = pd.date_range("2021-05-05", periods=360, freq="min", tz="UTC")
    frame = pd.DataFrame(
        {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "event_ts": timestamps,
            "close_ts": timestamps + pd.Timedelta(seconds=59, milliseconds=999),
            "decision_ts": timestamps + pd.Timedelta(seconds=59, milliseconds=999),
            "log_return_1": np.full(360, 0.001),
            "rolling_volatility_60": np.full(360, 0.0001),
            "warmup_row": [True] * 60 + [False] * 300,
            "row_valid_for_features": True,
            "feature_error_count": 0,
        }
    )

    labels = create_label_frame_v9_40(frame, "1m", "test_run")

    assert list(labels.columns) == REQUIRED_LABEL_COLUMNS
    valid = labels[labels["label_valid"]]
    assert not valid.empty
    assert (valid["label_available_ts"] > valid["decision_ts"]).all()
    assert set(valid["up_down_flat_volnorm_h4_5y"].dropna().unique()) <= {-1, 0, 1}
    assert labels["binary_directional_volnorm_h4_5y"].dropna().isin([-1, 1]).all()


def test_create_label_frame_marks_tail_unavailable() -> None:
    timestamps = pd.date_range("2021-05-05", periods=260, freq="min", tz="UTC")
    frame = pd.DataFrame(
        {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "event_ts": timestamps,
            "close_ts": timestamps + pd.Timedelta(seconds=59, milliseconds=999),
            "decision_ts": timestamps + pd.Timedelta(seconds=59, milliseconds=999),
            "log_return_1": np.full(260, 0.0001),
            "rolling_volatility_60": np.full(260, 0.0001),
            "warmup_row": False,
            "row_valid_for_features": True,
            "feature_error_count": 0,
        }
    )

    labels = create_label_frame_v9_40(frame, "1m", "test_run")

    assert (labels.tail(240)["label_invalid_reason"] == "future_horizon_unavailable").any()
    assert labels.tail(240)["label_valid"].sum() == 0
