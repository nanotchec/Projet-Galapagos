from __future__ import annotations

from galapagos.analysis.regime_diagnostics import (
    classify_window_regime,
    holding_time_analysis,
    side_performance_by_regime,
)


def test_regime_classification_uptrend_downtrend_range() -> None:
    uptrend = classify_window_regime(_ohlcv([100 + index for index in range(90)]))
    downtrend = classify_window_regime(_ohlcv([200 - index for index in range(90)]))
    range_market = classify_window_regime(_ohlcv([100 + (index % 3 - 1) for index in range(90)]))

    assert uptrend["regime_label"] == "uptrend"
    assert downtrend["regime_label"] == "downtrend"
    assert range_market["regime_label"] == "range"


def test_side_performance_by_regime_aggregates_long_short() -> None:
    result = side_performance_by_regime(
        [
            _trade("LONG", "uptrend", 10.0),
            _trade("SHORT", "uptrend", -5.0),
            _trade("SHORT", "downtrend", 7.0),
        ]
    )

    assert result["LONG_in_uptrend"]["trade_count"] == 1
    assert result["SHORT_in_uptrend"]["net_pnl"] == -5.0
    assert result["SHORT_in_downtrend"]["net_pnl"] == 7.0


def test_holding_time_buckets() -> None:
    result = holding_time_analysis(
        [
            _trade("LONG", "uptrend", 10.0, duration_bars=0.5),
            _trade("LONG", "uptrend", -2.0, duration_bars=2),
            _trade("LONG", "uptrend", 3.0, duration_bars=5),
            _trade("LONG", "uptrend", 4.0, duration_bars=8),
        ]
    )

    assert result["duration_buckets"]["<1 bougie"]["trade_count"] == 1
    assert result["duration_buckets"]["1-2 bougies"]["trade_count"] == 1
    assert result["duration_buckets"]["3-6 bougies"]["trade_count"] == 1
    assert result["duration_buckets"][">6 bougies"]["trade_count"] == 1


def test_report_payload_shape() -> None:
    regime = classify_window_regime(_ohlcv([100 + index for index in range(90)]))
    side = side_performance_by_regime([_trade("LONG", "uptrend", 10.0)])
    holding = holding_time_analysis([_trade("LONG", "uptrend", 10.0)])

    payload = {
        "window_regimes": {"calibration": regime},
        "side_performance_by_regime": side,
        "holding_time": holding,
        "holdout_executed": False,
    }
    assert payload["window_regimes"]["calibration"]["regime_label"] == "uptrend"
    assert payload["side_performance_by_regime"]["LONG_in_uptrend"]["trade_count"] == 1
    assert payload["holdout_executed"] is False


def _ohlcv(closes: list[float]):
    import pandas as pd

    rows = []
    start = pd.Timestamp("2026-01-01T00:00:00")
    for index, close in enumerate(closes):
        rows.append(
            {
                "timestamp": start + pd.Timedelta(hours=4 * index),
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 100,
            }
        )
    return pd.DataFrame(rows)


def _trade(
    side: str,
    regime: str,
    net_pnl: float,
    *,
    duration_bars: float = 2,
) -> dict:
    return {
        "side": side,
        "window_regime_label": regime,
        "gross_pnl": net_pnl + 1.0,
        "net_pnl": net_pnl,
        "fees": 0.5,
        "slippage": 0.5,
        "duration_bars": duration_bars,
        "duration_hours": duration_bars * 4,
        "exit_reason": "take_profit" if net_pnl > 0 else "stop_loss",
        "volatility_entry": 0.01,
    }
