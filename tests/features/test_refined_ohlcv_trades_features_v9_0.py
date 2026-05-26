from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from galapagos.features.refined_ohlcv_trades_schemas import (
    EXPECTED_ROWS_V9_0,
    MANIFEST_PATH_V9_0,
    REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0,
    REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0,
)


ROOT = Path(__file__).resolve().parents[2]


def _manifest() -> dict:
    return json.loads((ROOT / MANIFEST_PATH_V9_0).read_text(encoding="utf-8"))


def _frame(timeframe: str) -> pd.DataFrame:
    return pd.read_parquet(ROOT / _manifest()["outputs"][timeframe]["path"])


def test_refined_features_v9_0_row_counts_match_expected() -> None:
    manifest = _manifest()

    assert {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()} == EXPECTED_ROWS_V9_0


def test_refined_features_v9_0_schema_strict() -> None:
    frame = _frame("1h")

    assert list(frame.columns) == REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0


def test_refined_features_v9_0_uses_selected_features_only() -> None:
    manifest = _manifest()

    assert manifest["selected_features"] == REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0
    assert manifest["selected_features_count"] == 18
    assert manifest["dropped_features_absent"] is True


def test_refined_features_v9_0_no_forbidden_columns() -> None:
    forbidden_terms = ["future_", "label_", "direction_", "up_down_flat_", "prediction", "signal", "order", "pnl", "backtest"]

    assert not [column for column in REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0 if any(term in column for term in forbidden_terms)]


def test_refined_features_v9_0_time_order_and_causality() -> None:
    frame = _frame("15m")

    assert pd.to_datetime(frame["event_ts"], utc=True).is_monotonic_increasing
    assert (pd.to_datetime(frame["feature_available_ts"], utc=True) >= pd.to_datetime(frame["available_ts"], utc=True)).all()
    assert (pd.to_datetime(frame["decision_ts"], utc=True) >= pd.to_datetime(frame["feature_available_ts"], utc=True)).all()


def test_refined_features_v9_0_source_hashes_present() -> None:
    frame = _frame("5m")

    assert frame["source_v8_3_features_sha256"].nunique() == 1
    assert frame["source_feature_selection_sha256"].nunique() == 1
