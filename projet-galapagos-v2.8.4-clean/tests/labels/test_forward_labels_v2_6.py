from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from galapagos.labels.forward_returns import build_forward_labels
from galapagos.labels.schemas import LABEL_COLUMNS_V2_6
from galapagos.labels.registry import THRESHOLD


def test_build_forward_labels_mathematical_correctness():
    # 1. Create a dummy OHLCV DataFrame in memory
    # We need at least 10 rows to test horizons 1, 3, 5 comfortably.
    dates = pd.date_range("2024-01-15 00:00:00+00:00", periods=10, freq="1min")
    close_ts = [d.strftime("%Y-%m-%dT%H:%M:%S.%fZ") for d in dates]
    event_ts = close_ts
    available_ts = close_ts
    decision_ts = close_ts

    # dummy prices: close prices designed to test direction and up/down/flat threshold
    # threshold is 0.0005. 
    # log(100.1 / 100.0) = 0.0009995 > 0.0005 (UP)
    # log(99.9 / 100.0) = -0.0010005 < -0.0005 (DOWN)
    # log(100.02 / 100.0) = 0.00019998 < 0.0005 (FLAT)
    close_prices = [
        100.0,   # row 0
        100.1,   # row 1: up vs row 0
        99.9,    # row 2: down vs row 1
        100.02,  # row 3: flat vs row 2
        100.0,   # row 4
        101.0,   # row 5
        101.0,   # row 6
        102.0,   # row 7
        102.0,   # row 8
        103.0,   # row 9
    ]

    ohlcv_df = pd.DataFrame({
        "source": ["binance_archive"] * 10,
        "venue": ["binance"] * 10,
        "market_type": ["spot"] * 10,
        "symbol": ["BTCUSDT"] * 10,
        "timeframe": ["1m"] * 10,
        "open": close_prices,
        "high": close_prices,
        "low": close_prices,
        "close": close_prices,
        "volume": [1.0] * 10,
        "event_ts": event_ts,
        "close_ts": close_ts,
        "available_ts": available_ts,
        "decision_ts": decision_ts,
    })

    sha256 = "dummy_sha256_val"
    run_id = "test_run_123"

    # 2. Build labels
    labels_df = build_forward_labels(ohlcv_df, sha256, run_id)

    # 3. Assertions
    assert isinstance(labels_df, pd.DataFrame)
    assert list(labels_df.columns) == LABEL_COLUMNS_V2_6
    assert len(labels_df) == 10

    # Metadata assertions
    assert (labels_df["source_ohlcv_sha256"] == sha256).all()
    assert (labels_df["label_run_id"] == run_id).all()
    assert (labels_df["label_schema_version"] == "V2.6").all()

    # Mathematical assertions for row 0
    # Horizon 1: future close is at row 1 (100.1)
    # Simple Return = 100.1 / 100.0 - 1.0 = 0.001
    # Log Return = log(100.1 / 100.0) = 0.0009995
    # Direction = 1.0 (since return > 0)
    # Class = "UP" (since log return > 0.0005)
    # label_end_ts_h1 = close_ts[1]
    # label_valid_h1 = True
    assert labels_df.loc[0, "future_close_h1"] == 100.1
    assert abs(labels_df.loc[0, "future_simple_return_h1"] - 0.001) < 1e-8
    assert abs(labels_df.loc[0, "future_log_return_h1"] - np.log(100.1 / 100.0)) < 1e-8
    assert labels_df.loc[0, "direction_h1"] == 1.0
    assert labels_df.loc[0, "up_down_flat_h1"] == "UP"
    assert labels_df.loc[0, "label_end_ts_h1"] == close_ts[1]
    assert bool(labels_df.loc[0, "label_valid_h1"]) is True

    # Mathematical assertions for row 1 vs row 2 (down)
    # Horizon 1: future close is at row 2 (99.9) vs close at row 1 (100.1)
    # Log Return = log(99.9 / 100.1) = -0.00200000000000000000000000000
    assert labels_df.loc[1, "direction_h1"] == -1.0
    assert labels_df.loc[1, "up_down_flat_h1"] == "DOWN"

    # Mathematical assertions for row 2 vs row 3 (flat)
    # Horizon 1: future close is at row 3 (100.02) vs close at row 2 (99.9)
    # Log Return = log(100.02 / 99.9) = 0.00120048 > 0.0005 (actually UP!)
    # Let's check row 2 vs row 4 for flat
    # close_prices[2] = 99.9, close_prices[3] = 100.02. Let's make sure we test FLAT
    # log(100.02 / 100.1) = -0.000799 vs -0.0005 (DOWN)
    # Let's check a flat return: log(100.02 / 100.0) at row 3 vs 4 (100.0 vs 100.02)
    # Simple Return = 100.0 / 100.02 - 1.0 = -0.00019996
    # Log Return = log(100.0 / 100.02) = -0.00019998
    # direction_h1 at row 3 (future close = 100.0 vs close = 100.02) is -1.0
    # up_down_flat_h1 at row 3 is "FLAT" since abs(log_return) = 0.00019998 < 0.0005
    assert labels_df.loc[3, "direction_h1"] == -1.0
    assert labels_df.loc[3, "up_down_flat_h1"] == "FLAT"

    # Assertions for tail rows
    # The last 5 rows (indices 5, 6, 7, 8, 9) must have tail_row = True
    # Let's check row index 5:
    # Horizon 5: future close is shift(-5), which for index 5 is index 10 (None/NaN)
    # So label_valid_h5 must be False, making tail_row True.
    # For row index 4, future close h5 is index 9 (103.0), which is valid, so all horizons should be valid
    # So tail_row at row 4 must be False.
    assert bool(labels_df.loc[4, "tail_row"]) is False
    assert bool(labels_df.loc[5, "tail_row"]) is True
    assert bool(labels_df.loc[6, "tail_row"]) is True
    assert bool(labels_df.loc[7, "tail_row"]) is True
    assert bool(labels_df.loc[8, "tail_row"]) is True
    assert bool(labels_df.loc[9, "tail_row"]) is True

    # Assertions for invalid horizons
    # For index 9 (last row), all horizons are invalid. Check nullification
    for h in [1, 3, 5]:
        assert pd.isna(labels_df.loc[9, f"future_close_h{h}"])
        assert pd.isna(labels_df.loc[9, f"future_simple_return_h{h}"])
        assert pd.isna(labels_df.loc[9, f"future_log_return_h{h}"])
        assert pd.isna(labels_df.loc[9, f"direction_h{h}"])
        assert pd.isna(labels_df.loc[9, f"up_down_flat_h{h}"])
        assert pd.isna(labels_df.loc[9, f"label_end_ts_h{h}"])
        assert bool(labels_df.loc[9, f"label_valid_h{h}"]) is False

    # Check label_available_ts monotonicity and causal separation guard
    # label_available_ts for row 0 is label_end_ts_h5 (since valid) which is close_ts[5]
    # decision_ts for row 0 is close_ts[0]
    # close_ts[5] > close_ts[0], so separation is valid
    assert labels_df.loc[0, "label_available_ts"] == close_ts[5]
    assert pd.to_datetime(labels_df.loc[0, "label_available_ts"]) > pd.to_datetime(labels_df.loc[0, "decision_ts"])
