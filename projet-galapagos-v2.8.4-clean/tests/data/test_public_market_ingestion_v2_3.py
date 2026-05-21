from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.config import PublicMarketIngestionConfig
from galapagos.data.public_market.ingestion import normalize_binance_klines, run_public_market_ingestion
from galapagos.data.public_market.quality import assess_ohlcv_quality
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.sources.binance_archive import (
    build_public_archive_url,
    parse_binance_kline_csv,
)


def test_build_public_archive_url_uses_allowed_binance_host() -> None:
    url = build_public_archive_url(market_type="spot", symbol="BTCUSDT", timeframe="1m", date="2024-01-15")
    assert url == "https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01-15.zip"


def test_parse_binance_csv_columns_and_numeric_values() -> None:
    frame = parse_binance_kline_csv(_csv_rows(minutes=2))
    assert list(frame.columns) == [
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
        "event_ts",
        "close_ts",
        "source_timestamp_unit",
    ]
    assert frame.loc[0, "open"] == pytest.approx(42000.0)
    assert frame.loc[1, "trade_count"] == 101


def test_parse_binance_csv_converts_millisecond_timestamps_to_utc() -> None:
    frame = parse_binance_kline_csv(_csv_rows(minutes=1))
    assert str(frame["event_ts"].dt.tz) == "UTC"
    assert frame.loc[0, "event_ts"].isoformat().replace("+00:00", "Z") == "2024-01-15T00:00:00Z"
    assert frame.loc[0, "source_timestamp_unit"] == "ms"


def test_normalize_adds_expected_ohlcv_columns_and_metadata() -> None:
    raw = parse_binance_kline_csv(_csv_rows(minutes=2))
    config = PublicMarketIngestionConfig(
        source="binance_archive",
        market_type="spot",
        symbol="BTCUSDT",
        timeframe="1m",
        date="2024-01-15",
    )
    normalized = normalize_binance_klines(
        raw,
        config=config,
        raw_sha="abc",
        ingestion_run_id="run",
        ingested_at_ts="2024-01-16T00:00:00Z",
    )
    assert list(normalized.columns) == OHLCV_COLUMNS
    assert set(normalized["source"]) == {"binance_archive"}
    assert set(normalized["venue"]) == {"binance"}
    assert set(normalized["symbol"]) == {"BTCUSDT"}
    assert normalized["available_ts"].iloc[0] == normalized["close_ts"].iloc[0]
    assert normalized["decision_ts"].iloc[0] == normalized["available_ts"].iloc[0]


def test_quality_accepts_complete_monotonic_sample() -> None:
    frame = _normalized_frame(minutes=4)
    quality = assess_ohlcv_quality(frame, expected_rows=4, timeframe="1m")
    assert quality.passed is True
    assert quality.payload["rows"] == 4
    assert quality.payload["gap_count"] == 0
    assert quality.payload["duplicate_rows"] == 0


def test_quality_rejects_row_count_mismatch_as_error() -> None:
    frame = _normalized_frame(minutes=1439)
    quality = assess_ohlcv_quality(frame, expected_rows=1440, timeframe="1m")
    assert quality.passed is False
    assert any("rows 1439 != expected_rows 1440" in error for error in quality.payload["errors"])


def test_quality_rejects_physical_non_monotonic_order() -> None:
    frame = _normalized_frame(minutes=4)
    shuffled = frame.iloc[[0, 2, 1, 3]].reset_index(drop=True)
    quality = assess_ohlcv_quality(shuffled, expected_rows=4, timeframe="1m")
    assert quality.passed is False
    assert quality.payload["gap_count"] == 0
    assert quality.payload["monotonic_event_ts"] is False
    assert "event_ts is not monotonic increasing" in quality.payload["errors"]


def test_quality_detects_duplicate_rows() -> None:
    frame = _normalized_frame(minutes=3)
    duplicated = pd.concat([frame, frame.iloc[[1]]], ignore_index=True)
    quality = assess_ohlcv_quality(duplicated, expected_rows=4, timeframe="1m")
    assert quality.passed is False
    assert quality.payload["duplicate_rows"] == 1


def test_quality_detects_temporal_gap() -> None:
    frame = _normalized_frame(minutes=4).drop(index=2).reset_index(drop=True)
    quality = assess_ohlcv_quality(frame, expected_rows=4, timeframe="1m")
    assert quality.passed is False
    assert quality.payload["gap_count"] == 1
    assert quality.payload["gaps"][0]["delta_seconds"] == 120


def test_quality_detects_ohlc_violation() -> None:
    frame = _normalized_frame(minutes=2)
    frame.loc[0, "high"] = frame.loc[0, "low"] - 1
    quality = assess_ohlcv_quality(frame, expected_rows=2, timeframe="1m")
    assert quality.passed is False
    assert quality.payload["ohlc_violations"] == 1


def test_quality_detects_negative_volume() -> None:
    frame = _normalized_frame(minutes=2)
    frame.loc[0, "volume"] = -1.0
    quality = assess_ohlcv_quality(frame, expected_rows=2, timeframe="1m")
    assert quality.passed is False
    assert quality.payload["negative_volume_rows"] == 1


def test_quality_detects_null_critical_value() -> None:
    frame = _normalized_frame(minutes=2)
    frame.loc[0, "close"] = None
    quality = assess_ohlcv_quality(frame, expected_rows=2, timeframe="1m")
    assert quality.passed is False
    assert quality.payload["null_critical_rows"] == 1


def test_run_no_network_requires_existing_raw_archive(tmp_path: Path) -> None:
    config = _config(tmp_path, no_network=True)
    with pytest.raises(FileNotFoundError, match="raw public archive"):
        run_public_market_ingestion(config)


def test_run_no_network_uses_existing_raw_and_writes_manifest_and_parquet(tmp_path: Path) -> None:
    _write_raw_zip(tmp_path, minutes=1440)
    manifest = run_public_market_ingestion(_config(tmp_path, no_network=True))
    assert manifest["status"] == "PASS"
    assert manifest["network_used"] is False
    assert manifest["quality"]["rows"] == 1440
    assert Path(manifest["silver"]["path"]).exists()
    assert Path(manifest["raw"]["path"]).exists()
    silver = pd.read_parquet(manifest["silver"]["path"])
    assert "normalized_file_sha256" not in silver.columns


def _config(tmp_path: Path, *, no_network: bool = False) -> PublicMarketIngestionConfig:
    return PublicMarketIngestionConfig(
        source="binance_archive",
        market_type="spot",
        symbol="BTCUSDT",
        timeframe="1m",
        date="2024-01-15",
        output_root=tmp_path,
        no_network=no_network,
    )


def _normalized_frame(*, minutes: int) -> pd.DataFrame:
    raw = parse_binance_kline_csv(_csv_rows(minutes=minutes))
    return normalize_binance_klines(
        raw,
        config=PublicMarketIngestionConfig(
            source="binance_archive",
            market_type="spot",
            symbol="BTCUSDT",
            timeframe="1m",
            date="2024-01-15",
        ),
        raw_sha="raw-sha",
        ingestion_run_id="run-id",
        ingested_at_ts="2024-01-16T00:00:00Z",
    )


def _write_raw_zip(tmp_path: Path, *, minutes: int) -> Path:
    config = _config(tmp_path, no_network=True)
    config.raw_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(config.raw_path, "w") as archive:
        archive.writestr("BTCUSDT-1m-2024-01-15.csv", _csv_rows(minutes=minutes))
    return config.raw_path


def _csv_rows(*, minutes: int) -> str:
    rows = []
    start = pd.Timestamp("2024-01-15T00:00:00Z")
    for index in range(minutes):
        open_ts = int((start + pd.Timedelta(minutes=index)).timestamp() * 1000)
        close_ts = int((start + pd.Timedelta(minutes=index, seconds=59, milliseconds=999)).timestamp() * 1000)
        open_price = 42000.0 + index
        rows.append(
            ",".join(
                [
                    str(open_ts),
                    f"{open_price:.2f}",
                    f"{open_price + 10:.2f}",
                    f"{open_price - 10:.2f}",
                    f"{open_price + 1:.2f}",
                    "12.5",
                    str(close_ts),
                    "525000.0",
                    str(100 + index),
                    "6.25",
                    "262500.0",
                    "0",
                ]
            )
        )
    return "\n".join(rows) + "\n"
