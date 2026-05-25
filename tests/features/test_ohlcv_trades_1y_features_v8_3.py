from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.features.ohlcv_trades_1y import (
    EXPECTED_ROWS_V8_3,
    MANIFEST_PATH_V8_3,
    TIMEFRAMES_V8_3,
    WINDOW_END_V8_3,
    WINDOW_START_V8_3,
    input_ohlcv_path,
    load_v5_0_ohlcv_manifest,
    output_path,
)
from galapagos.features.ohlcv_trades_1y_schemas import OHLCV_TRADES_FEATURE_COLUMNS_V8_3


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def v8_3_manifest(project_root: Path) -> dict:
    return json.loads((project_root / MANIFEST_PATH_V8_3).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def feature_paths(project_root: Path) -> dict[str, Path]:
    return {
        timeframe: output_path(project_root, timeframe, WINDOW_START_V8_3, WINDOW_END_V8_3)
        for timeframe in TIMEFRAMES_V8_3
    }


@pytest.fixture(scope="session")
def frame_1m(feature_paths: dict[str, Path]) -> pd.DataFrame:
    return pd.read_parquet(feature_paths["1m"], engine="pyarrow")


@pytest.fixture(scope="session")
def frame_1h(feature_paths: dict[str, Path]) -> pd.DataFrame:
    return pd.read_parquet(feature_paths["1h"], engine="pyarrow")


def test_ohlcv_trades_1y_features_row_count_matches_expected_bars(feature_paths: dict[str, Path]) -> None:
    for timeframe, path in feature_paths.items():
        assert pq.ParquetFile(path).metadata.num_rows == EXPECTED_ROWS_V8_3[timeframe]


def test_ohlcv_trades_1y_features_strict_columns(feature_paths: dict[str, Path]) -> None:
    for path in feature_paths.values():
        assert pq.ParquetFile(path).schema.names == OHLCV_TRADES_FEATURE_COLUMNS_V8_3


def test_ohlcv_trades_1y_aggregation_has_positive_counts(frame_1m: pd.DataFrame) -> None:
    assert (frame_1m["agg_trade_count"] > 0).all()
    assert (frame_1m["agg_trade_quantity_sum"] > 0).all()
    assert (frame_1m["agg_trade_quote_quantity_sum"] > 0).all()


def test_ohlcv_trades_1y_taker_buy_ratios_bounded(frame_1m: pd.DataFrame) -> None:
    for column in ["taker_buy_ratio_count", "taker_buy_ratio_quantity", "taker_buy_ratio_quote"]:
        clean = frame_1m[column].dropna()
        assert ((clean >= 0.0) & (clean <= 1.0)).all()


def test_ohlcv_trades_1y_imbalance_bounded(frame_1m: pd.DataFrame) -> None:
    for column in ["taker_imbalance_count", "taker_imbalance_quantity", "taker_imbalance_quote"]:
        clean = frame_1m[column].dropna()
        assert ((clean >= -1.0) & (clean <= 1.0)).all()


def test_ohlcv_trades_1y_feature_available_ts_not_before_available_ts(feature_paths: dict[str, Path]) -> None:
    for path in feature_paths.values():
        frame = pd.read_parquet(path, columns=["feature_available_ts", "available_ts"], engine="pyarrow")
        assert (pd.to_datetime(frame["feature_available_ts"], utc=True) >= pd.to_datetime(frame["available_ts"], utc=True)).all()


def test_ohlcv_trades_1y_decision_ts_not_before_feature_available_ts(feature_paths: dict[str, Path]) -> None:
    for path in feature_paths.values():
        frame = pd.read_parquet(path, columns=["decision_ts", "feature_available_ts"], engine="pyarrow")
        assert (pd.to_datetime(frame["decision_ts"], utc=True) >= pd.to_datetime(frame["feature_available_ts"], utc=True)).all()


def test_ohlcv_trades_1y_no_forbidden_feature_columns(frame_1h: pd.DataFrame) -> None:
    forbidden = {"future_return", "future_close", "label", "target", "prediction", "signal", "trading_signal", "order", "pnl", "backtest"}
    assert not (set(frame_1h.columns) & forbidden)


def test_ohlcv_trades_1y_volume_consistency_metrics_present(v8_3_manifest: dict) -> None:
    for timeframe in TIMEFRAMES_V8_3:
        quality = v8_3_manifest["quality"][timeframe]
        assert "median_volume_relative_diff" in quality
        assert "median_quote_volume_relative_diff" in quality
        assert quality["median_volume_relative_diff"] is not None
        assert quality["median_quote_volume_relative_diff"] is not None


def test_ohlcv_trades_1y_source_hashes_match_inputs(
    project_root: Path,
    feature_paths: dict[str, Path],
    v8_3_manifest: dict,
) -> None:
    v5_manifest = load_v5_0_ohlcv_manifest(project_root)
    trades_manifest_sha = sha256_file(project_root / "reports/manifests/public_trades_1y_window_v8_2_manifest.json")
    for timeframe, path in feature_paths.items():
        hashes = pd.read_parquet(path, columns=["source_ohlcv_sha256", "source_trades_manifest_sha256"], engine="pyarrow")
        expected_ohlcv_sha = sha256_file(input_ohlcv_path(project_root, timeframe, v5_manifest))
        assert set(hashes["source_ohlcv_sha256"].astype(str).unique()) == {expected_ohlcv_sha}
        assert set(hashes["source_trades_manifest_sha256"].astype(str).unique()) == {trades_manifest_sha}
        assert v8_3_manifest["input_ohlcv"][timeframe]["sha256"] == expected_ohlcv_sha
