from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

from galapagos.data.ohlcv_5y_extension_v9_34 import (
    EXPECTED_ROWS_BY_TIMEFRAME,
    TIMEFRAMES,
    build_ohlcv_diagnostic_v9_34,
    collect_or_normalize_day_v9_34,
    date_range_v9_34,
    normalize_klines_for_v9_34,
    validate_ohlcv_frame_v9_34,
)


def test_v9_34_missing_window_day_count_and_timeframes() -> None:
    assert len(date_range_v9_34("2021-05-05", "2023-03-24")) == 689
    assert set(TIMEFRAMES) == {"1m", "5m", "15m", "1h"}


def test_v9_34_normalized_schema_and_quality_accept_valid_daily_frame() -> None:
    raw = _raw_kline_frame("2021-05-05", "1m", EXPECTED_ROWS_BY_TIMEFRAME["1m"])
    normalized = normalize_klines_for_v9_34(raw, timeframe="1m", day="2021-05-05", source_file="raw.zip")

    result = validate_ohlcv_frame_v9_34(normalized, timeframe="1m", day="2021-05-05")

    assert result["passed"] is True
    assert result["duplicate_open_time_count"] == 0
    assert result["timestamp_gap_warnings"] == 0
    assert normalized["available_ts"].equals(normalized["close_ts"])
    assert normalized["decision_ts"].equals(normalized["close_ts"])


def test_v9_34_quality_rejects_duplicate_open_time() -> None:
    raw = _raw_kline_frame("2021-05-05", "5m", EXPECTED_ROWS_BY_TIMEFRAME["5m"])
    normalized = normalize_klines_for_v9_34(raw, timeframe="5m", day="2021-05-05", source_file="raw.zip")
    normalized.loc[1, "open_ts"] = normalized.loc[0, "open_ts"]

    result = validate_ohlcv_frame_v9_34(normalized, timeframe="5m", day="2021-05-05")

    assert result["passed"] is False
    assert any("duplicate open_time" in error for error in result["errors"])


def test_v9_34_collect_day_uses_fake_public_downloader_and_writes_silver(tmp_path: Path) -> None:
    source_zip = tmp_path / "source.zip"
    _write_kline_zip(source_zip, "BTCUSDT-1h-2021-05-05.csv", _csv_text("2021-05-05", "1h", 24))

    def fake_downloader(url: str, destination: Path) -> None:
        assert url == "https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1h/BTCUSDT-1h-2021-05-05.zip"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source_zip.read_bytes())

    result = collect_or_normalize_day_v9_34(tmp_path, "1h", "2021-05-05", downloader=fake_downloader)

    assert result.status == "day_complete"
    assert result.network_used is True
    assert result.rows == 24
    assert Path(result.silver_path).is_file()


def test_v9_34_diagnostic_combines_daily_silver_and_research_windows(tmp_path: Path) -> None:
    for timeframe in TIMEFRAMES:
        research = tmp_path / f"data/research/v5_0/silver/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window=2023-03-25_2026-05-23/ohlcv.parquet"
        research.parent.mkdir(parents=True, exist_ok=True)
        research.write_bytes(b"metadata")
        silver = tmp_path / f"data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/year=2021/month=05/part-2021-05-05.parquet"
        silver.parent.mkdir(parents=True, exist_ok=True)
        silver.write_bytes(b"metadata")

    diagnostic = build_ohlcv_diagnostic_v9_34(tmp_path, {"v5_0_manifest": {"available": True}})

    assert diagnostic["available_days_by_timeframe"]["1m"] == 1139
    assert diagnostic["missing_days_by_timeframe"]["1m"] == 688
    assert diagnostic["ohlcv_5y_ready"] is False


def _raw_kline_frame(day: str, timeframe: str, rows: int) -> pd.DataFrame:
    delta = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h"}[timeframe]
    open_ts = pd.date_range(day, periods=rows, freq=delta, tz="UTC")
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
            "event_ts": open_ts,
            "close_ts": close_ts,
        }
    )


def _csv_text(day: str, timeframe: str, rows: int) -> str:
    frame = _raw_kline_frame(day, timeframe, rows)
    columns = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "trade_count", "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"]
    return frame[columns].to_csv(index=False, header=False)


def _write_kline_zip(path: Path, inner_name: str, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(inner_name, content)
