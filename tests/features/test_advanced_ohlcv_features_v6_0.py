from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.features.advanced_ohlcv import TIMEFRAMES_V6_0, input_ohlcv_path, load_v5_0_ohlcv_manifest, output_path
from galapagos.features.advanced_ohlcv_schemas import (
    ADVANCED_OHLCV_FEATURE_COLUMNS_V6_0,
    ADVANCED_OHLCV_FEATURE_FAMILIES_V6_0,
)


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def v5_0_manifest(project_root: Path) -> dict:
    return load_v5_0_ohlcv_manifest(project_root)


@pytest.fixture(scope="session")
def v6_0_manifest(project_root: Path) -> dict:
    return json.loads((project_root / "reports/manifests/advanced_ohlcv_feature_store_v6_0_manifest.json").read_text())


@pytest.fixture(scope="session")
def feature_paths(project_root: Path, v5_0_manifest: dict) -> dict[str, Path]:
    window_start = v5_0_manifest["discovery"]["window_start"]
    window_end = v5_0_manifest["discovery"]["window_end"]
    return {timeframe: output_path(project_root, timeframe, window_start, window_end) for timeframe in TIMEFRAMES_V6_0}


@pytest.fixture(scope="session")
def frame_1h(feature_paths: dict[str, Path]) -> pd.DataFrame:
    return pd.read_parquet(feature_paths["1h"], engine="pyarrow")


@pytest.fixture(scope="session")
def input_1h(project_root: Path, v5_0_manifest: dict) -> pd.DataFrame:
    return pd.read_parquet(input_ohlcv_path(project_root, "1h", v5_0_manifest), engine="pyarrow")


def test_advanced_features_row_count_matches_input(
    project_root: Path,
    v5_0_manifest: dict,
    feature_paths: dict[str, Path],
) -> None:
    for timeframe, feature_path in feature_paths.items():
        input_path = input_ohlcv_path(project_root, timeframe, v5_0_manifest)
        assert pq.ParquetFile(feature_path).metadata.num_rows == pq.ParquetFile(input_path).metadata.num_rows
        assert pq.ParquetFile(feature_path).metadata.num_rows == v5_0_manifest["expected_rows"][timeframe]


def test_advanced_features_strict_columns(feature_paths: dict[str, Path]) -> None:
    for path in feature_paths.values():
        assert pq.ParquetFile(path).schema.names == ADVANCED_OHLCV_FEATURE_COLUMNS_V6_0


def test_advanced_features_have_all_families(frame_1h: pd.DataFrame) -> None:
    for family, columns in ADVANCED_OHLCV_FEATURE_FAMILIES_V6_0.items():
        assert columns, family
        assert set(columns).issubset(frame_1h.columns)


def test_advanced_returns_are_past_only(frame_1h: pd.DataFrame, input_1h: pd.DataFrame) -> None:
    assert pd.isna(frame_1h.loc[0, "return_1"])
    assert frame_1h.loc[10, "return_10"] == pytest.approx(input_1h.loc[10, "close"] / input_1h.loc[0, "close"] - 1.0)
    assert frame_1h.loc[60, "log_return_60"] == pytest.approx(np.log(input_1h.loc[60, "close"] / input_1h.loc[0, "close"]))


def test_advanced_rolling_features_have_expected_warmup(feature_paths: dict[str, Path]) -> None:
    for path in feature_paths.values():
        frame = pd.read_parquet(path, columns=["warmup_row", "advanced_feature_null_count"], engine="pyarrow")
        warmup_rows = int(frame["warmup_row"].sum())
        assert warmup_rows >= 120
        assert bool(frame.loc[:119, "warmup_row"].all())
        first_clean = frame.index[frame["advanced_feature_null_count"] == 0][0]
        assert not bool(frame.loc[first_clean, "warmup_row"])


def test_advanced_temporal_features_utc(frame_1h: pd.DataFrame) -> None:
    event_ts = pd.to_datetime(frame_1h["event_ts"], utc=True)
    assert (frame_1h["hour_utc"].to_numpy() == event_ts.dt.hour.to_numpy()).all()
    assert (frame_1h["day_of_week_utc"].to_numpy() == event_ts.dt.dayofweek.to_numpy()).all()
    assert (frame_1h["month_utc"].to_numpy() == event_ts.dt.month.to_numpy()).all()
    assert (frame_1h["quarter_utc"].to_numpy() == event_ts.dt.quarter.to_numpy()).all()
    assert (frame_1h["is_weekend_utc"].to_numpy() == event_ts.dt.dayofweek.isin([5, 6]).to_numpy()).all()


def test_advanced_feature_available_ts_not_before_available_ts(feature_paths: dict[str, Path]) -> None:
    for path in feature_paths.values():
        frame = pd.read_parquet(path, columns=["feature_available_ts", "available_ts"], engine="pyarrow")
        assert (pd.to_datetime(frame["feature_available_ts"], utc=True) >= pd.to_datetime(frame["available_ts"], utc=True)).all()


def test_advanced_decision_ts_not_before_feature_available_ts(feature_paths: dict[str, Path]) -> None:
    for path in feature_paths.values():
        frame = pd.read_parquet(path, columns=["decision_ts", "feature_available_ts"], engine="pyarrow")
        assert (pd.to_datetime(frame["decision_ts"], utc=True) >= pd.to_datetime(frame["feature_available_ts"], utc=True)).all()


def test_advanced_no_forbidden_feature_columns(frame_1h: pd.DataFrame) -> None:
    forbidden_exact = {"future_return", "future_close", "label", "target", "prediction", "signal", "order", "pnl", "backtest"}
    assert not (set(frame_1h.columns) & forbidden_exact)


def test_advanced_source_hashes_match_inputs(
    project_root: Path,
    v5_0_manifest: dict,
    feature_paths: dict[str, Path],
) -> None:
    for timeframe, path in feature_paths.items():
        source_hashes = pd.read_parquet(path, columns=["source_ohlcv_sha256"], engine="pyarrow")
        expected_sha = sha256_file(input_ohlcv_path(project_root, timeframe, v5_0_manifest))
        assert set(source_hashes["source_ohlcv_sha256"].astype(str).unique()) == {expected_sha}


def test_advanced_no_global_future_quantile_leakage(frame_1h: pd.DataFrame) -> None:
    assert (frame_1h["volatility_regime_low"].fillna(False).to_numpy() == (frame_1h["vol_zscore_120"] < -0.5).fillna(False).to_numpy()).all()
    assert (frame_1h["volume_regime_high"].fillna(False).to_numpy() == (frame_1h["rolling_volume_zscore_120"] > 0.5).fillna(False).to_numpy()).all()


def test_advanced_taker_buy_features_bounded_reasonably(frame_1h: pd.DataFrame) -> None:
    ratio = frame_1h["taker_buy_base_ratio"].dropna()
    imbalance = frame_1h["taker_buy_imbalance"].dropna()
    assert ((ratio >= 0.0) & (ratio <= 1.0)).all()
    assert ((imbalance >= -1.0) & (imbalance <= 1.0)).all()


def test_advanced_bollinger_features_consistent(frame_1h: pd.DataFrame) -> None:
    clean = frame_1h.dropna(subset=["bollinger_upper_20", "bollinger_mid_20", "bollinger_lower_20", "bollinger_width_20"])
    assert (clean["bollinger_upper_20"] >= clean["bollinger_mid_20"]).all()
    assert (clean["bollinger_mid_20"] >= clean["bollinger_lower_20"]).all()
    expected_width = (clean["bollinger_upper_20"] - clean["bollinger_lower_20"]) / clean["bollinger_mid_20"]
    assert np.allclose(clean["bollinger_width_20"], expected_width, rtol=1e-5, atol=1e-7)


def test_advanced_donchian_features_consistent(frame_1h: pd.DataFrame) -> None:
    clean = frame_1h.dropna(subset=["rolling_high_60", "rolling_low_60", "donchian_width_60"])
    assert (clean["rolling_high_60"] >= clean["rolling_low_60"]).all()
    assert (clean["donchian_width_60"] >= 0.0).all()
