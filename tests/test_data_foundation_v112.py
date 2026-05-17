from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.binance_public_archive import (
    build_binance_archive_url,
    parse_binance_kline_csv,
    plan_binance_ohlcv_download,
)
from galapagos.data.ccxt_historical import plan_ccxt_ohlcv_fetch
from galapagos.data.derivatives.alignment import align_derivatives_asof
from galapagos.data.derivatives.features import causal_zscore
from galapagos.data.derivatives.schema import DerivativesRecord
from galapagos.data.macro.fred_client import build_fred_observations_url
from galapagos.data.macro.fred_collector import parse_fred_observations
from galapagos.data.macro.macro_features import build_macro_features
from galapagos.data.manifest import create_manifest, redact_request_params
from galapagos.research.research_dataset import join_asof_causal, validate_no_future_features
from galapagos.utils.secrets import redact_secret, safe_env_status


def test_secret_redaction_and_env_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FRED_API_KEY", "very-secret-value")
    assert safe_env_status(["FRED_API_KEY"]) == {"FRED_API_KEY": "configured"}
    assert "very-secret-value" not in redact_secret("very-secret-value")


def test_manifest_redacts_request_params(tmp_path: Path) -> None:
    file_path = tmp_path / "data.csv"
    file_path.write_text("a\n1\n", encoding="utf-8")
    manifest = create_manifest(
        dataset_id="test",
        source="unit",
        symbol="BTC",
        timeframe="4h",
        file_path=file_path,
        rows=1,
        request_params={"api_key": "secret", "symbol": "BTC"},
    )
    encoded = json.dumps(manifest.to_dict())
    assert "secret" not in encoded
    assert manifest.request_params_redacted["api_key"] == "configured"
    assert redact_request_params({"token": "abc"})["token"] == "configured"


def test_binance_archive_url_parser_and_resume() -> None:
    url = build_binance_archive_url(
        symbol="BTCUSDT",
        market="futures_um",
        interval="4h",
        year=2024,
        month=1,
    )
    assert "BTCUSDT-4h-2024-01.zip" in url
    csv = "1,100,110,90,105,10,2,0,1,0,0,0\n"
    frame = parse_binance_kline_csv(csv)
    assert frame["close"].iloc[0] == 105.0
    plans = plan_binance_ohlcv_download(
        symbol="BTCUSDT",
        market="futures_um",
        interval="4h",
        years=1,
    )
    assert plans


def test_ccxt_dry_run_planner() -> None:
    plan = plan_ccxt_ohlcv_fetch(
        exchange="kraken",
        symbol="BTC/USD",
        timeframe="4h",
        years=3,
        dry_run=True,
    )
    assert plan.dry_run is True
    assert plan.estimated_pages > 0


def test_derivatives_schema_alignment_and_zscore() -> None:
    record = DerivativesRecord(
        timestamp="2024-01-01T00:00:00Z",
        available_timestamp="2024-01-01T04:00:00Z",
        source="binance",
        symbol="BTCUSDT",
        metric_name="funding_rate",
        metric_value=0.01,
        metadata_json={},
    )
    assert record.to_dict()["metric_name"] == "funding_rate"
    base = pd.DataFrame({"timestamp": pd.date_range("2024-01-01", periods=3, freq="4h", tz="UTC")})
    features = pd.DataFrame(
        {
            "available_timestamp": [pd.Timestamp("2024-01-01T04:00:00Z")],
            "funding_rate": [0.01],
        }
    )
    aligned = align_derivatives_asof(base, features)
    assert "funding_rate" in aligned.columns
    zscore = causal_zscore(pd.Series([1.0, 2.0, 3.0, 4.0]), window=3)
    assert pd.isna(zscore.iloc[0])


def test_fred_mock_parser_and_macro_features() -> None:
    url = build_fred_observations_url("DFF", "2020-01-01", "secret")
    assert "series_id=DFF" in url
    parsed = parse_fred_observations("DFF", [{"date": "2020-01-01", "value": "1.5"}])
    assert parsed["value"].iloc[0] == 1.5
    features = build_macro_features(parsed)
    assert "macro_regime" in features.columns


def test_causal_join_and_future_rejection() -> None:
    base = pd.DataFrame({"timestamp": pd.date_range("2024-01-01", periods=2, freq="4h", tz="UTC")})
    features = pd.DataFrame(
        {
            "available_timestamp": [pd.Timestamp("2024-01-01T00:00:00Z")],
            "feature": [1.0],
        }
    )
    joined = join_asof_causal(base, features)
    assert validate_no_future_features(joined)
    bad = base.copy()
    bad["available_timestamp"] = pd.Timestamp("2024-01-02T00:00:00Z")
    with pytest.raises(ValueError):
        validate_no_future_features(bad)
