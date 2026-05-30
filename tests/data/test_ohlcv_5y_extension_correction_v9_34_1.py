from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

from galapagos.data.ohlcv_5y_extension_correction_v9_34_1 import (
    BAD_DAY,
    BAD_TIMEFRAME,
    diagnose_bad_day_v9_34_1,
    repair_bad_day_if_needed_v9_34_1,
)
from galapagos.data.ohlcv_5y_extension_v9_34 import (
    EXPECTED_ROWS_BY_TIMEFRAME,
    raw_kline_path_v9_34,
    silver_ohlcv_path_v9_34,
    validate_silver_day_v9_34,
)


def test_v9_34_1_bad_day_diagnostic_detects_incomplete_1m_raw(tmp_path: Path) -> None:
    raw_path = raw_kline_path_v9_34(tmp_path, BAD_TIMEFRAME, BAD_DAY)
    _write_kline_zip(raw_path, BAD_DAY, BAD_TIMEFRAME, rows=1170, gap_after_index=400)

    diagnostic = diagnose_bad_day_v9_34_1(tmp_path)

    assert diagnostic["raw_exists"] is True
    assert diagnostic["zip_readable"] is True
    assert diagnostic["csv_member_count"] == 1
    assert diagnostic["row_count"] == 1170
    assert diagnostic["expected_row_count"] == EXPECTED_ROWS_BY_TIMEFRAME[BAD_TIMEFRAME]
    assert diagnostic["timestamp_gap_count"] == 1
    assert diagnostic["local_raw_incomplete_or_invalid"] is True


def test_v9_34_1_repair_redownloads_valid_bad_day_and_rebuilds_silver(tmp_path: Path) -> None:
    raw_path = raw_kline_path_v9_34(tmp_path, BAD_TIMEFRAME, BAD_DAY)
    _write_kline_zip(raw_path, BAD_DAY, BAD_TIMEFRAME, rows=1170, gap_after_index=400)
    diagnostic = diagnose_bad_day_v9_34_1(tmp_path)

    def fake_downloader(url: str, destination: Path) -> None:
        assert "data.binance.vision" in url
        assert f"BTCUSDT-{BAD_TIMEFRAME}-{BAD_DAY}.zip" in url
        _write_kline_zip(destination, BAD_DAY, BAD_TIMEFRAME, rows=1440)

    repair = repair_bad_day_if_needed_v9_34_1(tmp_path, diagnostic, downloader=fake_downloader)
    silver_path = silver_ohlcv_path_v9_34(tmp_path, BAD_TIMEFRAME, BAD_DAY)
    silver_validation = validate_silver_day_v9_34(silver_path, timeframe=BAD_TIMEFRAME, day=BAD_DAY)

    assert repair["redownload_attempted"] is True
    assert repair["redownload_success"] is True
    assert repair["redownload_row_count"] == 1440
    assert repair["redownload_quality_status"] == "PASS"
    assert repair["repair_status"] == "repaired"
    assert repair["silver_rebuilt_for_2021_08_13"] is True
    assert repair["backup_raw_path"] is not None
    assert Path(repair["backup_raw_path"]).is_file()
    assert silver_validation["passed"] is True
    assert silver_validation["rows"] == 1440


def test_v9_34_1_repair_refuses_still_incomplete_redownload(tmp_path: Path) -> None:
    raw_path = raw_kline_path_v9_34(tmp_path, BAD_TIMEFRAME, BAD_DAY)
    _write_kline_zip(raw_path, BAD_DAY, BAD_TIMEFRAME, rows=1170, gap_after_index=400)
    diagnostic = diagnose_bad_day_v9_34_1(tmp_path)

    def fake_downloader(_url: str, destination: Path) -> None:
        _write_kline_zip(destination, BAD_DAY, BAD_TIMEFRAME, rows=1170, gap_after_index=400)

    repair = repair_bad_day_if_needed_v9_34_1(tmp_path, diagnostic, downloader=fake_downloader)

    assert repair["redownload_attempted"] is True
    assert repair["redownload_success"] is False
    assert repair["redownload_row_count"] == 1170
    assert repair["redownload_quality_status"] == "FAIL"
    assert repair["repair_status"] == "source_issue"
    assert not silver_ohlcv_path_v9_34(tmp_path, BAD_TIMEFRAME, BAD_DAY).exists()


def _write_kline_zip(path: Path, day: str, timeframe: str, *, rows: int, gap_after_index: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = _csv_text(day, timeframe, rows=rows, gap_after_index=gap_after_index)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"BTCUSDT-{timeframe}-{day}.csv", content)


def _csv_text(day: str, timeframe: str, *, rows: int, gap_after_index: int | None) -> str:
    frame = _raw_kline_frame(day, timeframe, rows=rows, gap_after_index=gap_after_index)
    columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "trade_count",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
        "ignore",
    ]
    return frame[columns].to_csv(index=False, header=False)


def _raw_kline_frame(day: str, timeframe: str, *, rows: int, gap_after_index: int | None) -> pd.DataFrame:
    delta = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h"}[timeframe]
    open_ts = pd.date_range(day, periods=rows, freq=delta, tz="UTC")
    if gap_after_index is not None:
        open_ts = open_ts.to_series().reset_index(drop=True)
        open_ts.loc[gap_after_index + 1 :] = open_ts.loc[gap_after_index + 1 :] + pd.Timedelta(delta)
        open_ts = pd.DatetimeIndex(open_ts)
    close_ts = open_ts + pd.Timedelta(delta) - pd.Timedelta(milliseconds=1)
    return pd.DataFrame(
        {
            "open_time": (open_ts.view("int64") // 1_000_000).astype("int64"),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 10.0,
            "close_time": (close_ts.view("int64") // 1_000_000).astype("int64"),
            "quote_volume": 1000.0,
            "trade_count": 12,
            "taker_buy_base_volume": 5.0,
            "taker_buy_quote_volume": 500.0,
            "ignore": 0,
        }
    )
