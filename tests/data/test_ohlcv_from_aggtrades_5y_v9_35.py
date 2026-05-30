from __future__ import annotations

from pathlib import Path

import pandas as pd

from galapagos.data.ohlcv_from_aggtrades_5y_v9_35 import (
    DERIVED_COLUMNS,
    EXPECTED_ROWS_BY_TIMEFRAME,
    TIMEFRAMES,
    date_range_v9_35,
    derive_1m_day_from_aggtrades_v9_35,
    derived_output_path_v9_35,
    resample_derived_ohlcv_v9_35,
    validate_derived_ohlcv_frame_v9_35,
)


def test_v9_35_target_window_has_expected_day_count() -> None:
    assert len(date_range_v9_35("2021-05-05", "2026-05-05")) == 1827
    assert set(TIMEFRAMES) == {"1m", "5m", "15m", "1h"}
    assert EXPECTED_ROWS_BY_TIMEFRAME["1m"] == 2_630_880


def test_v9_35_derives_causal_1m_bucket_from_aggtrades() -> None:
    frame = _aggtrades_frame(
        [
            ("2021-05-05T00:00:00.100Z", 10, 100.0, 1.0, False),
            ("2021-05-05T00:00:20.000Z", 11, 105.0, 2.0, True),
            ("2021-05-05T00:00:59.999Z", 12, 101.0, 3.0, False),
            ("2021-05-05T00:01:01.000Z", 13, 102.0, 4.0, True),
        ]
    )

    derived = derive_1m_day_from_aggtrades_v9_35(frame, day="2021-05-05")
    first = derived.iloc[0]
    second = derived.iloc[1]

    assert list(derived.columns) == DERIVED_COLUMNS
    assert len(derived) == 1440
    assert first["open"] == 100.0
    assert first["high"] == 105.0
    assert first["low"] == 100.0
    assert first["close"] == 101.0
    assert first["volume"] == 6.0
    assert first["quote_volume"] == 613.0
    assert first["trades_count"] == 3
    assert first["taker_buy_base_volume"] == 4.0
    assert first["taker_buy_quote_volume"] == 403.0
    assert second["open"] == 102.0
    assert first["available_ts"] == first["close_ts"]
    assert first["ohlcv_source_type"] == "derived_from_aggtrades"


def test_v9_35_resamples_derived_1m_into_5m_without_future_data() -> None:
    one_minute = derive_1m_day_from_aggtrades_v9_35(
        _aggtrades_frame(
            [
                ("2021-05-05T00:00:00.000Z", 1, 100.0, 1.0, False),
                ("2021-05-05T00:04:59.000Z", 2, 110.0, 2.0, False),
                ("2021-05-05T00:05:00.000Z", 3, 90.0, 3.0, True),
            ]
        ),
        day="2021-05-05",
    )

    five_minute = resample_derived_ohlcv_v9_35(one_minute, "5m")
    first = five_minute.iloc[0]
    second = five_minute.iloc[1]

    assert first["open"] == 100.0
    assert first["high"] == 110.0
    assert first["low"] == 100.0
    assert first["close"] == 110.0
    assert first["volume"] == 3.0
    assert first["trades_count"] == 2
    assert second["open"] == 90.0


def test_v9_35_validation_rejects_missing_rows() -> None:
    frame = derive_1m_day_from_aggtrades_v9_35(
        _aggtrades_frame([("2021-05-05T00:00:00.000Z", 1, 100.0, 1.0, False)]),
        day="2021-05-05",
    )

    result = validate_derived_ohlcv_frame_v9_35(frame, timeframe="1m")

    assert result["quality_status"] == "FAIL"
    assert result["days_missing"] == 1826
    assert result["invalid_rows"] == 1439


def test_v9_35_output_path_marks_source_type_and_window(tmp_path: Path) -> None:
    path = derived_output_path_v9_35(tmp_path, "1h")

    assert "data/research/v9_35/ohlcv_from_aggtrades" in path.as_posix()
    assert "timeframe=1h" in path.as_posix()
    assert "window=2021-05-05_2026-05-05" in path.as_posix()


def _aggtrades_frame(rows: list[tuple[str, int, float, float, bool]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_ts": [row[0] for row in rows],
            "aggregate_trade_id": [row[1] for row in rows],
            "price": [row[2] for row in rows],
            "quantity": [row[3] for row in rows],
            "is_buyer_maker": [row[4] for row in rows],
            "row_valid": True,
        }
    )
