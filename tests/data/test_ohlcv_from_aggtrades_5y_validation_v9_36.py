from __future__ import annotations

import pandas as pd

from galapagos.data.ohlcv_from_aggtrades_5y_validation_v9_36 import (
    FORBIDDEN_COLUMNS,
    analyze_zero_trade_buckets_v9_36,
    compute_invariant_counts_v9_36,
    date_range_v9_36,
    max_consecutive_true_v9_36,
)


def test_v9_36_target_window_has_expected_days() -> None:
    assert len(date_range_v9_36("2021-05-05", "2026-05-05")) == 1827


def test_v9_36_invariant_counts_accept_valid_frame() -> None:
    frame = pd.DataFrame({"open": [100.0], "high": [101.0], "low": [99.0], "close": [100.5], "volume": [0.0], "quote_volume": [0.0], "trades_count": [0]})
    open_ts = pd.Series(pd.to_datetime(["2021-05-05T00:00:00Z"], utc=True))
    close_ts = pd.Series(pd.to_datetime(["2021-05-05T00:00:59.999Z"], utc=True))

    counts = compute_invariant_counts_v9_36(frame, open_ts, close_ts, open_ts, close_ts, close_ts)

    assert all(value == 0 for value in counts.values())


def test_v9_36_zero_trade_fill_is_non_blocking_when_previous_close_is_used() -> None:
    frame = _frame_with_zero_trade_bucket()

    result = analyze_zero_trade_buckets_v9_36(frame, timeframe="1m")

    assert result["zero_trade_bucket_count"] == 1
    assert result["ohlc_equals_previous_close"] is True
    assert result["volume_zero_confirmed"] is True
    assert result["trades_count_zero_confirmed"] is True
    assert result["causal_fill_uses_future_data"] is False
    assert result["zero_trade_buckets_blocking"] is False


def test_v9_36_zero_trade_fill_blocks_when_ohlc_uses_non_previous_value() -> None:
    frame = _frame_with_zero_trade_bucket()
    frame.loc[1, "close"] = 99.0

    result = analyze_zero_trade_buckets_v9_36(frame, timeframe="1m")

    assert result["ohlc_equals_previous_close"] is False
    assert result["zero_trade_buckets_blocking"] is True


def test_v9_36_forbidden_columns_include_trading_and_label_surfaces() -> None:
    assert {"prediction", "trading_signal", "order", "pnl", "label", "target"}.issubset(FORBIDDEN_COLUMNS)


def test_v9_36_max_consecutive_true_counts_runs() -> None:
    assert max_consecutive_true_v9_36([False, True, True, False, True, True, True]) == 3


def _frame_with_zero_trade_bucket() -> pd.DataFrame:
    open_ts = pd.to_datetime(["2021-05-05T00:00:00Z", "2021-05-05T00:01:00Z"], utc=True)
    close_ts = open_ts + pd.Timedelta(minutes=1) - pd.Timedelta(milliseconds=1)
    return pd.DataFrame(
        {
            "open_ts": open_ts,
            "close_ts": close_ts,
            "available_ts": close_ts,
            "open": [100.0, 100.5],
            "high": [101.0, 100.5],
            "low": [99.0, 100.5],
            "close": [100.5, 100.5],
            "volume": [5.0, 0.0],
            "quote_volume": [500.0, 0.0],
            "trades_count": [2, 0],
        }
    )
